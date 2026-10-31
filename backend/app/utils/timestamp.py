from datetime import datetime, timezone
from typing import Optional
import re


def parse_iso_or_standard_timestamp(ts_str: str) -> Optional[datetime]:
    """Parses various timestamp representations into a Python datetime object.
    
    Supports:
    - ISO 8601: '2026-10-30T14:22:15.123Z', '2026-10-30T14:22:15+00:00'
    - Standard SQL: '2026-10-30 14:22:15', '2026-10-30 14:22:15.500'
    - Date only: '2026-10-30'
    - Epoch seconds / milliseconds
    """
    if not ts_str:
        return None

    clean_str = str(ts_str).strip()

    # Check for Unix epoch (numeric)
    if re.match(r"^\d{10}(\.\d+)?$", clean_str):
        try:
            return datetime.fromtimestamp(float(clean_str), tz=timezone.utc).replace(tzinfo=None)
        except Exception:
            pass

    if re.match(r"^\d{13}$", clean_str):  # Epoch millis
        try:
            return datetime.fromtimestamp(float(clean_str) / 1000.0, tz=timezone.utc).replace(tzinfo=None)
        except Exception:
            pass

    # ISO formats
    try:
        dt = datetime.fromisoformat(clean_str.replace("Z", "+00:00"))
        return dt.replace(tzinfo=None)
    except Exception:
        pass

    # Fallback common formats
    formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d",
        "%H:%M:%S",
        "%H:%M:%S.%f",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(clean_str, fmt)
        except ValueError:
            continue

    return None


def format_iso_timestamp(dt: Optional[datetime]) -> Optional[str]:
    """Formats datetime to ISO 8601 string."""
    if not dt:
        return None
    return dt.isoformat()
