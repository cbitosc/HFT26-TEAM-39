from datetime import datetime
import enum
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, Text
from sqlalchemy.orm import relationship

from app.database import Base


class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    RECONSTRUCTED = "RECONSTRUCTED"
    CLOSED = "CLOSED"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    incident_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(
        SAEnum(IncidentStatus),
        default=IncidentStatus.OPEN,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    evidence = relationship("Evidence", back_populates="incident", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="incident", cascade="all, delete-orphan", order_by="Event.timestamp")
    vehicles = relationship("Vehicle", back_populates="incident", cascade="all, delete-orphan")
