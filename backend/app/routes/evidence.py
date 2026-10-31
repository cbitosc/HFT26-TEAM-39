import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.evidence import Evidence
from app.models.event import Event
from app.schemas.evidence import (
    EvidenceResponse,
    EvidenceUploadResponse,
    EvidenceDetailResponse,
    FileIntegrityInfo,
)
from app.services.evidence_service import evidence_service

router = APIRouter(tags=["Evidence"])


@router.post(
    "/api/incidents/{incident_id}/evidence",
    response_model=EvidenceUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence(
    incident_id: str,
    file: UploadFile = File(..., description="Evidence file (.mp4, .mov, .avi, .txt, .pdf, .csv)"),
    description: Optional[str] = Form(None, description="Optional description of the evidence item"),
    vehicle_id: Optional[str] = Form(None, description="Optional associated vehicle identifier"),
    db: Session = Depends(get_db),
):
    """Uploads an evidence file, computes its SHA-256 cryptographic digest, and logs metadata."""
    record = await evidence_service.store_evidence_file(
        db=db,
        incident_id=incident_id,
        upload_file=file,
        description=description,
        vehicle_id=vehicle_id,
    )

    return EvidenceUploadResponse(
        evidence_id=record.id,
        incident_id=record.incident_id,
        filename=record.filename,
        file_type=record.file_type,
        file_size_bytes=record.file_size_bytes,
        sha256_hash=record.sha256_hash,
        integrity_notice=settings.INTEGRITY_DISCLAIMER,
        upload_timestamp=record.upload_timestamp,
    )


@router.get(
    "/api/incidents/{incident_id}/evidence",
    response_model=List[EvidenceResponse],
)
def list_incident_evidence(incident_id: str, db: Session = Depends(get_db)):
    """Lists all evidence items associated with an incident."""
    records = evidence_service.list_evidence_by_incident(db, incident_id)
    results = []
    for r in records:
        meta = json.loads(r.metadata_json) if r.metadata_json else None
        results.append(
            EvidenceResponse(
                id=r.id,
                incident_id=r.incident_id,
                filename=r.filename,
                original_filename=r.original_filename,
                file_type=r.file_type,
                mime_type=r.mime_type,
                file_size_bytes=r.file_size_bytes,
                sha256_hash=r.sha256_hash,
                description=r.description,
                vehicle_id=r.vehicle_id,
                upload_timestamp=r.upload_timestamp,
                is_processed=r.is_processed,
                metadata=meta,
            )
        )
    return results


@router.get(
    "/api/evidence/{evidence_id}",
    response_model=EvidenceDetailResponse,
)
def get_evidence_detail(evidence_id: str, db: Session = Depends(get_db)):
    """Retrieves detailed evidence metadata including SHA-256 integrity details and linked events."""
    r = evidence_service.get_evidence_by_id(db, evidence_id)
    meta = json.loads(r.metadata_json) if r.metadata_json else {}

    # Count events referencing this evidence
    events = db.query(Event).filter(Event.source_evidence_ids.contains(r.id)).count()

    integrity_info = FileIntegrityInfo(
        sha256_hash=r.sha256_hash,
        file_size_bytes=r.file_size_bytes,
        integrity_notice=settings.INTEGRITY_DISCLAIMER,
    )

    return EvidenceDetailResponse(
        id=r.id,
        incident_id=r.incident_id,
        filename=r.filename,
        original_filename=r.original_filename,
        file_type=r.file_type,
        mime_type=r.mime_type,
        file_size_bytes=r.file_size_bytes,
        sha256_hash=r.sha256_hash,
        description=r.description,
        vehicle_id=r.vehicle_id,
        upload_timestamp=r.upload_timestamp,
        is_processed=r.is_processed,
        metadata=meta,
        integrity_info=integrity_info,
        linked_event_count=events,
    )


@router.delete("/api/evidence/{evidence_id}")
def delete_evidence(evidence_id: str, db: Session = Depends(get_db)):
    """Deletes an evidence file and its database record."""
    return evidence_service.delete_evidence(db, evidence_id)
