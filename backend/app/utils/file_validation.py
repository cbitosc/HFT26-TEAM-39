import hashlib
from pathlib import Path
from typing import Tuple
from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.models.evidence import EvidenceFileType

# Supported extensions mapping to evidence types
SUPPORTED_EXTENSIONS = {
    # Video files
    ".mp4": EvidenceFileType.VIDEO,
    ".mov": EvidenceFileType.VIDEO,
    ".avi": EvidenceFileType.VIDEO,
    # Witness statements
    ".txt": EvidenceFileType.WITNESS_STATEMENT,
    ".pdf": EvidenceFileType.WITNESS_STATEMENT,
    # Telemetry
    ".csv": EvidenceFileType.TELEMETRY,
}

# Permitted MIME types
PERMITTED_MIME_TYPES = {
    # Video
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/avi",
    # Text / Document
    "text/plain",
    "application/pdf",
    # CSV / Delimited
    "text/csv",
    "application/vnd.ms-excel",
    "application/octet-stream",  # Fallback for some clients
}


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 cryptographic digest of a file.
    
    Technical Purpose:
    Verifies that the byte stream stored in the filesystem exactly matches
    the original uploaded byte stream, guarding against corruption or silent
    tampering. Does NOT verify physical authenticity or source provenance.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_file_extension_and_type(filename: str) -> Tuple[str, EvidenceFileType]:
    """Validates the file extension against allowed types."""
    if not filename or "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has no extension. Allowed extensions: .mp4, .mov, .avi, .txt, .pdf, .csv",
        )

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(SUPPORTED_EXTENSIONS.keys())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{suffix}'. Allowed: {allowed}",
        )

    return suffix, SUPPORTED_EXTENSIONS[suffix]


def validate_file_size(size_bytes: int) -> None:
    """Ensures file does not exceed maximum configured upload size."""
    if size_bytes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if size_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum permitted upload size of {max_mb} MB.",
        )
