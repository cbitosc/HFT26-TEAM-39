from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.models.evidence import EvidenceFileType


class FileIntegrityInfo(BaseModel):
    sha256_hash: str = Field(..., description="Cryptographic SHA-256 digest of file contents")
    file_size_bytes: int
    integrity_notice: str = Field(
        ...,
        description="Notice clarifying integrity verification vs origin authenticity",
    )


class EvidenceResponse(BaseModel):
    id: str
    incident_id: str
    filename: str
    original_filename: str
    file_type: EvidenceFileType
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    description: Optional[str] = None
    vehicle_id: Optional[str] = None
    upload_timestamp: datetime
    is_processed: bool
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class EvidenceUploadResponse(BaseModel):
    evidence_id: str
    incident_id: str
    filename: str
    file_type: EvidenceFileType
    file_size_bytes: int
    sha256_hash: str
    integrity_notice: str
    upload_timestamp: datetime
    message: str = "Evidence file successfully uploaded, validated, and hashed."


class EvidenceDetailResponse(EvidenceResponse):
    integrity_info: FileIntegrityInfo
    linked_event_count: int = 0
