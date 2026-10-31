import json
import logging
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.evidence import Evidence, EvidenceFileType
from app.models.incident import Incident
from app.models.event import Event
from app.utils.file_validation import (
    compute_sha256,
    validate_file_extension_and_type,
    validate_file_size,
)

logger = logging.getLogger(__name__)


class EvidenceService:
    """Manages the forensic chain of custody, storage, and hashing for evidence files."""

    async def store_evidence_file(
        self,
        db: Session,
        incident_id: str,
        upload_file: UploadFile,
        description: Optional[str] = None,
        vehicle_id: Optional[str] = None,
    ) -> Evidence:
        """Stores evidence file to disk, computes SHA-256 hash, and records metadata."""
        # 1. Verify incident exists
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with ID '{incident_id}' not found.",
            )

        # 2. Validate filename and extension
        original_filename = upload_file.filename or "unknown_file"
        suffix, file_type = validate_file_extension_and_type(original_filename)

        # 3. Create incident-specific storage folder
        incident_dir = settings.UPLOAD_DIR / incident_id
        incident_dir.mkdir(parents=True, exist_ok=True)

        evidence_id = f"EVD-{uuid.uuid4().hex[:10].upper()}"
        safe_filename = f"{evidence_id}{suffix}"
        target_path = incident_dir / safe_filename

        # 4. Stream write file to preserve exact byte sequence (NEVER alter contents)
        total_bytes = 0
        try:
            with open(target_path, "wb") as f_out:
                while chunk := await upload_file.read(1024 * 64):
                    total_bytes += len(chunk)
                    if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                        # Clean up partial file on disk
                        f_out.close()
                        if target_path.exists():
                            target_path.unlink()
                        validate_file_size(total_bytes)
                    f_out.write(chunk)
        except HTTPException:
            raise
        except Exception as e:
            if target_path.exists():
                target_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to write evidence file to disk: {str(e)}",
            )

        validate_file_size(total_bytes)

        # 5. Compute cryptographic SHA-256 hash
        sha256_hash = compute_sha256(target_path)

        # Extract initial technical metadata
        meta: Dict[str, Any] = {
            "original_filename": original_filename,
            "saved_filename": safe_filename,
            "byte_size": total_bytes,
            "file_extension": suffix,
            "storage_path": str(target_path),
            "integrity_verification": "SHA-256",
            "integrity_notice": settings.INTEGRITY_DISCLAIMER,
        }

        # 6. Save record to database
        evidence_record = Evidence(
            id=evidence_id,
            incident_id=incident_id,
            filename=safe_filename,
            original_filename=original_filename,
            file_type=file_type,
            mime_type=upload_file.content_type or "application/octet-stream",
            file_size_bytes=total_bytes,
            file_path=str(target_path),
            sha256_hash=sha256_hash,
            description=description,
            vehicle_id=vehicle_id,
            upload_timestamp=datetime.utcnow(),
            metadata_json=json.dumps(meta),
            is_processed=False,
        )

        db.add(evidence_record)
        db.commit()
        db.refresh(evidence_record)
        logger.info("Stored evidence %s for incident %s (SHA256: %s)", evidence_id, incident_id, sha256_hash)
        return evidence_record

    def get_evidence_by_id(self, db: Session, evidence_id: str) -> Evidence:
        """Retrieves single evidence item or raises 404."""
        record = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence with ID '{evidence_id}' not found.",
            )
        return record

    def list_evidence_by_incident(self, db: Session, incident_id: str) -> List[Evidence]:
        """Lists all evidence files linked to an incident."""
        return db.query(Evidence).filter(Evidence.incident_id == incident_id).all()

    def delete_evidence(self, db: Session, evidence_id: str) -> Dict[str, Any]:
        """Deletes evidence record and associated disk file safely."""
        record = self.get_evidence_by_id(db, evidence_id)
        file_path = Path(record.file_path)

        # Remove physical file from disk
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError as e:
                logger.warning("Could not delete file from disk: %s", str(e))

        db.delete(record)
        db.commit()

        return {
            "evidence_id": evidence_id,
            "status": "DELETED",
            "message": "Evidence record and associated file removed.",
        }


# Global singleton
evidence_service = EvidenceService()
