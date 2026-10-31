from datetime import datetime
import enum
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, Float, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class EventClassification(str, enum.Enum):
    DIRECT_OBSERVATION = "DIRECT_OBSERVATION"
    DERIVED_VALUE = "DERIVED_VALUE"
    AI_INFERENCE = "AI_INFERENCE"
    MODEL_ASSUMPTION = "MODEL_ASSUMPTION"


class EventType(str, enum.Enum):
    VEHICLE_APPROACH = "VEHICLE_APPROACH"
    SPEED_CHANGE = "SPEED_CHANGE"
    ACCELERATION = "ACCELERATION"
    DECELERATION = "DECELERATION"
    BRAKE_ACTIVATION = "BRAKE_ACTIVATION"
    VEHICLE_STOPPING = "VEHICLE_STOPPING"
    IMPACT_COLLISION = "IMPACT_COLLISION"
    VIDEO_OBSERVATION = "VIDEO_OBSERVATION"
    WITNESS_REPORTED = "WITNESS_REPORTED"
    TELEMETRY_ANOMALY = "TELEMETRY_ANOMALY"


class Event(Base):
    __tablename__ = "events"

    id = Column(String(64), primary_key=True, index=True)
    incident_id = Column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    vehicle_id = Column(String(64), nullable=True, index=True)
    event_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    source_evidence_ids = Column(Text, nullable=False, default="[]")  # JSON string list
    source_row_numbers = Column(Text, nullable=False, default="[]")    # JSON string list of ints
    classification = Column(
        SAEnum(EventClassification),
        nullable=False,
        default=EventClassification.DIRECT_OBSERVATION,
    )
    confidence = Column(Float, nullable=True)
    raw_data = Column(Text, nullable=True)  # JSON-encoded raw observation details
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="events")
