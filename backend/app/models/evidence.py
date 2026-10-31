from datetime import datetime
import enum
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, Integer, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class EvidenceFileType(str, enum.Enum):
    VIDEO = "VIDEO"
    WITNESS_STATEMENT = "WITNESS_STATEMENT"
    TELEMETRY = "TELEMETRY"
    OTHER = "OTHER"


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String(64), primary_key=True, index=True)
    incident_id = Column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(SAEnum(EvidenceFileType), nullable=False)
    mime_type = Column(String(128), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_path = Column(String(512), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    vehicle_id = Column(String(64), nullable=True)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata_json = Column(Text, nullable=True)  # JSON-encoded technical metadata
    is_processed = Column(Boolean, default=False, nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="evidence")
