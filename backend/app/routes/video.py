from datetime import datetime, timedelta
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.models.evidence import Evidence, EvidenceFileType
from app.models.event import EventClassification, EventType
from app.schemas.analysis import (
    VideoProcessRequest,
    VideoProcessResponse,
    VideoDetectionEvent,
)
from app.services.video_service import video_service
from app.services.timeline_service import timeline_service

router = APIRouter(prefix="/api/incidents/{incident_id}/video", tags=["Video & Computer Vision"])


@router.post("/process", response_model=VideoProcessResponse)
def process_incident_video(
    incident_id: str,
    payload: VideoProcessRequest,
    db: Session = Depends(get_db),
):
    """Processes uploaded video evidence using OpenCV computer vision algorithms.
    
    Extracts frame rate, resolution, optical flow magnitude, and candidate vehicle detections.
    Generates structured timeline events without embedding CV logic in route handlers.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    evidence = db.query(Evidence).filter(
        Evidence.id == payload.evidence_id,
        Evidence.incident_id == incident_id,
    ).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence '{payload.evidence_id}' not found for this incident.",
        )

    if evidence.file_type != EvidenceFileType.VIDEO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evidence '{payload.evidence_id}' is of type '{evidence.file_type}', expected VIDEO.",
        )

    video_path = Path(evidence.file_path)
    if not video_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video file does not exist on disk at {video_path}",
        )

    # Call Computer Vision Service
    try:
        cv_results = video_service.analyze_video(
            video_path=video_path,
            sample_rate_frames=payload.sample_rate_frames,
            evidence_id=payload.evidence_id,
            incident_id=incident_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Computer vision analysis error: {str(e)}",
        )

    # Convert detected CV events to timeline events
    created_events_count = 0
    base_time = incident.incident_date

    for dev in cv_results["events_detected"]:
        offset_sec = dev["timestamp_offset_seconds"]
        event_time = base_time + timedelta(seconds=offset_sec)

        event_class = (
            EventClassification.DERIVED_VALUE
            if dev["event_type"] == "ANOMALOUS_MOTION_SPIKE"
            else EventClassification.DIRECT_OBSERVATION
        )

        timeline_service.create_event(
            db=db,
            incident_id=incident_id,
            timestamp=event_time,
            event_type=dev["event_type"],
            description=f"[Video Analysis] {dev['description']}",
            classification=event_class,
            vehicle_id=evidence.vehicle_id,
            source_evidence_ids=[evidence.id],
            source_row_numbers=[dev["frame_number"]],
            confidence=dev["confidence"],
            raw_data=dev,
        )
        created_events_count += 1

    # Update evidence metadata
    existing_meta = json.loads(evidence.metadata_json) if evidence.metadata_json else {}
    existing_meta["cv_analysis"] = {
        "frame_count": cv_results["frame_count"],
        "fps": cv_results["fps"],
        "duration_seconds": cv_results["duration_seconds"],
        "resolution": cv_results["resolution"],
        "events_count": len(cv_results["events_detected"]),
    }
    evidence.metadata_json = json.dumps(existing_meta)
    evidence.is_processed = True
    db.commit()

    return VideoProcessResponse(
        incident_id=incident_id,
        evidence_id=evidence.id,
        frame_count=cv_results["frame_count"],
        fps=cv_results["fps"],
        duration_seconds=cv_results["duration_seconds"],
        resolution=cv_results["resolution"],
        events_detected=[VideoDetectionEvent(**ev) for ev in cv_results["events_detected"]],
        timeline_events_created=created_events_count,
        cv_engine_notes=cv_results["cv_engine_notes"],
    )
