from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.incident import IncidentStatus


class IncidentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Incident title or reference name")
    location: str = Field(..., min_length=2, max_length=255, description="Geographic location or intersection")
    incident_date: datetime = Field(..., description="Date and time when the accident occurred")
    description: str = Field(..., min_length=5, description="Detailed narrative description of the accident")
    status: Optional[IncidentStatus] = Field(default=IncidentStatus.OPEN, description="Current investigation status")


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    location: Optional[str] = Field(None, min_length=2, max_length=255)
    incident_date: Optional[datetime] = None
    description: Optional[str] = Field(None, min_length=5)
    status: Optional[IncidentStatus] = None


class IncidentResponse(IncidentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IncidentDetailResponse(IncidentResponse):
    evidence_count: int = 0
    event_count: int = 0
    vehicle_ids: List[str] = []

    class Config:
        from_attributes = True
