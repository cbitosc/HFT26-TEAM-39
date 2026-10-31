import os
from pathlib import Path
from typing import List

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    from pydantic import BaseModel as BaseSettings, Field  # type: ignore

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "TRACE AI — Road Accident Investigation & Reconstruction"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'trace_ai.db'}")

    # File storage
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(100 * 1024 * 1024)))  # 100MB

    # Featherless AI Settings (server-side only)
    FEATHERLESS_API_KEY: str = os.getenv("FEATHERLESS_API_KEY", "rc_936bdec0715d0dd8c8499eb7ec1e96e9eefa67034dbabdd56345cc099c340442")
    FEATHERLESS_MODEL: str = os.getenv("FEATHERLESS_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
    FEATHERLESS_BASE_URL: str = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1").rstrip("/")

    # CORS settings
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,*"
        ).split(",")
        if origin.strip()
    ]

    # Verification disclaimer
    INTEGRITY_DISCLAIMER: str = (
        "SHA-256 digest verifies file integrity against post-upload modification or bit corruption. "
        "It establishes technical integrity of the stored record, not authentic origin or legal chain of custody."
    )

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure uploads directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
