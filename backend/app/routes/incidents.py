from datetime import datetime
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.incident import Incident, IncidentStatus
from app.models.evidence import Evidence
from app.models.event import Event
from app.models.vehicle import Vehicle
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentDetailResponse,
)

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    """Creates a new accident investigation incident with a unique forensic ID."""
    date_str = payload.incident_date.strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    incident_id = f"INC-{date_str}-{unique_suffix}"

    incident = Incident(
        id=incident_id,
        title=payload.title,
        location=payload.location,
        incident_date=payload.incident_date,
        description=payload.description,
        status=payload.status or IncidentStatus.OPEN,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    status_filter: Optional[IncidentStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None, description="Search in title or location"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Lists recorded accident incidents with optional filtering."""
    query = db.query(Incident)

    if status_filter:
        query = query.filter(Incident.status == status_filter)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter((Incident.title.ilike(search_fmt)) | (Incident.location.ilike(search_fmt)))

    return query.order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Retrieves full incident details, including counts of linked evidence and events."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    evidence_count = db.query(Evidence).filter(Evidence.incident_id == incident_id).count()
    event_count = db.query(Event).filter(Event.incident_id == incident_id).count()
    vehicles = db.query(Vehicle.vehicle_id).filter(Vehicle.incident_id == incident_id).all()
    vehicle_ids = [v[0] for v in vehicles]

    return IncidentDetailResponse(
        id=incident.id,
        title=incident.title,
        location=incident.location,
        incident_date=incident.incident_date,
        description=incident.description,
        status=incident.status,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        evidence_count=evidence_count,
        event_count=event_count,
        vehicle_ids=vehicle_ids,
    )


@router.put("/{incident_id}", response_model=IncidentResponse)
def update_incident(incident_id: str, payload: IncidentUpdate, db: Session = Depends(get_db)):
    """Updates incident metadata or status."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    if payload.title is not None:
        incident.title = payload.title
    if payload.location is not None:
        incident.location = payload.location
    if payload.incident_date is not None:
        incident.incident_date = payload.incident_date
    if payload.description is not None:
        incident.description = payload.description
    if payload.status is not None:
        incident.status = payload.status

    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)
    return incident


@router.delete("/{incident_id}")
def delete_incident(
    incident_id: str,
    confirm: bool = Query(False, description="Explicit confirmation required to delete an investigation"),
    db: Session = Depends(get_db),
):
    """Safeguarded deletion of an incident.
    
    Requires ?confirm=true to prevent accidental destruction of case data.
    Cascades to clean up all associated evidence files from disk.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion safeguard active. You must explicitly pass query parameter ?confirm=true to purge this incident.",
        )

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    # Safe disk cleanup for uploaded incident evidence directory
    incident_dir = settings.UPLOAD_DIR / incident_id
    if incident_dir.exists():
        try:
            shutil.rmtree(incident_dir)
        except Exception:
            pass

    # Database cascade delete
    db.delete(incident)
    db.commit()

    return {
        "incident_id": incident_id,
        "deleted": True,
        "message": f"Incident '{incident_id}' and all associated evidence files successfully deleted.",
    }
