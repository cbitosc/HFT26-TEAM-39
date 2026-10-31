from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.event import EventClassification
from app.schemas.timeline import (
    TimelineEventCreate,
    TimelineEventResponse,
    TimelineReconstructionResponse,
)
from app.services.timeline_service import timeline_service

router = APIRouter(prefix="/api/incidents/{incident_id}/timeline", tags=["Timeline"])


@router.get("", response_model=TimelineReconstructionResponse)
def get_incident_timeline(
    incident_id: str,
    vehicle_id: Optional[str] = Query(None, description="Filter timeline to a specific vehicle"),
    classification: Optional[EventClassification] = Query(None, description="Filter by epistemic classification"),
    db: Session = Depends(get_db),
):
    """Retrieves the deterministic, chronologically sorted timeline reconstruction for an incident."""
    class_val = classification.value if classification else None
    return timeline_service.get_chronological_timeline(
        db=db,
        incident_id=incident_id,
        vehicle_id=vehicle_id,
        classification=class_val,
    )


@router.post("/event", response_model=TimelineEventResponse, status_code=status.HTTP_201_CREATED)
def add_timeline_event(
    incident_id: str,
    payload: TimelineEventCreate,
    db: Session = Depends(get_db),
):
    """Manually records an observational or reconstructed event in the incident timeline."""
    event = timeline_service.create_event(
        db=db,
        incident_id=incident_id,
        timestamp=payload.timestamp,
        event_type=payload.event_type,
        description=payload.description,
        classification=payload.classification,
        vehicle_id=payload.vehicle_id,
        source_evidence_ids=payload.source_evidence_ids,
        source_row_numbers=payload.source_row_numbers,
        confidence=payload.confidence,
        raw_data=payload.raw_data,
    )
    return event
