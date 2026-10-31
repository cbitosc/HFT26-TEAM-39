from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.event import EventClassification


class TimelineEventBase(BaseModel):
    timestamp: datetime
    vehicle_id: Optional[str] = None
    event_type: str = Field(..., description="Type of kinematic or observational event")
    description: str = Field(..., description="Factual description of the event")
    source_evidence_ids: List[str] = Field(default_factory=list, description="IDs of source evidence files")
    source_row_numbers: List[int] = Field(default_factory=list, description="Source CSV row numbers or text line numbers")
    classification: EventClassification = Field(
        ...,
        description="Epistemic nature: DIRECT_OBSERVATION, DERIVED_VALUE, AI_INFERENCE, or MODEL_ASSUMPTION"
    )
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score if applicable")
    raw_data: Optional[Dict[str, Any]] = None


class TimelineEventCreate(TimelineEventBase):
    pass


class TimelineEventResponse(TimelineEventBase):
    id: str
    incident_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class TimelineReconstructionResponse(BaseModel):
    incident_id: str
    total_events: int
    chronological_order_verified: bool = True
    classifications_breakdown: Dict[str, int]
    vehicle_ids: List[str]
    time_span: Optional[Dict[str, Optional[datetime]]] = None
    events: List[TimelineEventResponse]
