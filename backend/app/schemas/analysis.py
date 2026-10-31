from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Telemetry Processing Schemas
class TelemetryProcessRequest(BaseModel):
    evidence_id: str = Field(..., description="ID of the uploaded CSV telemetry evidence")


class TelemetryObservation(BaseModel):
    row_number: int = Field(..., description="Original 1-indexed row number in the CSV")
    timestamp: str
    vehicle_id: str
    speed_kmh: Optional[float] = None
    acceleration_mps2: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    brake_status: Optional[str] = None
    throttle_position_pct: Optional[float] = None
    data_source: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    flagged_issues: List[str] = Field(default_factory=list)


class TelemetryVehicleSummary(BaseModel):
    vehicle_id: str
    data_points: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    min_speed_kmh: Optional[float] = None
    max_speed_kmh: Optional[float] = None
    avg_speed_kmh: Optional[float] = None
    max_deceleration_mps2: Optional[float] = None
    brake_activations_count: int = 0


class TelemetryProcessResponse(BaseModel):
    incident_id: str
    evidence_id: str
    total_rows: int
    valid_rows: int
    rows_with_missing_fields: int
    vehicles: List[TelemetryVehicleSummary]
    events_generated: int
    integrity_verified: bool
    summary: str


# Video Processing Schemas
class VideoProcessRequest(BaseModel):
    evidence_id: str = Field(..., description="ID of the uploaded video evidence")
    sample_rate_frames: int = Field(default=5, ge=1, le=60, description="Process every Nth frame for optical flow/motion analysis")


class VideoDetectionEvent(BaseModel):
    frame_number: int
    timestamp_offset_seconds: float
    event_type: str
    description: str
    motion_magnitude: float
    confidence: float
    bounding_boxes: List[Dict[str, Any]] = Field(default_factory=list)


class VideoProcessResponse(BaseModel):
    incident_id: str
    evidence_id: str
    frame_count: int
    fps: float
    duration_seconds: float
    resolution: str
    events_detected: List[VideoDetectionEvent]
    timeline_events_created: int
    cv_engine_notes: str


# Witness Analysis Schemas
class WitnessClaim(BaseModel):
    claim_id: str
    claim_type: str  # SPEED_CLAIM, TIME_CLAIM, BRAKE_CLAIM, DIRECTION_CLAIM, VEHICLE_CLAIM
    text_quote: str
    interpreted_value: Optional[str] = None
    claimed_vehicle_id: Optional[str] = None
    confidence: float = 1.0


class WitnessAnalysisRequest(BaseModel):
    evidence_id: str = Field(..., description="ID of witness statement (TXT or PDF)")


class WitnessAnalysisResponse(BaseModel):
    incident_id: str
    evidence_id: str
    witness_name_or_id: str
    statement_length_chars: int
    claims_extracted: List[WitnessClaim]
    events_created: int
    ai_status: str
    method_used: str  # "FEATHERLESS_AI" or "DETERMINISTIC_EXTRACTION_FALLBACK"


# Contradiction Analysis Schemas
class ContradictionItem(BaseModel):
    contradiction_id: str
    category: str  # TIMESTAMP_CONFLICT, SPEED_CONFLICT, MOVEMENT_CONFLICT, VEHICLE_DESCRIPTION_CONFLICT, MISSING_EVIDENCE, UNRESOLVED_DISCREPANCY
    description: str
    source_a: Dict[str, Any] = Field(..., description="First evidence source details (evidence_id, type, claim, rows)")
    source_b: Dict[str, Any] = Field(..., description="Second evidence source details (evidence_id, type, claim, rows)")
    discrepancy_details: str
    investigative_guidance: str = Field(
        default="Investigative Neutrality: Neither source is automatically presumed correct. Verification requires independent physical reconstruction.",
        description="Neutrality mandate disclaimer"
    )


class ContradictionAnalysisResponse(BaseModel):
    incident_id: str
    total_contradictions: int
    categories_breakdown: Dict[str, int]
    contradictions: List[ContradictionItem]
    investigative_summary: str
    ai_explanation: Optional[str] = None
    ai_available: bool = False


# AI Summary & Status Schemas
class AIStatusResponse(BaseModel):
    is_available: bool
    provider: str
    model: str
    base_url: str
    message: str


class AIConfigureRequest(BaseModel):
    api_key: str = Field(..., min_length=5, description="Featherless AI secret API key")
    model: Optional[str] = Field(None, description="Optional Featherless model identifier")


class AISummaryRequest(BaseModel):
    incident_id: str
    focus_areas: Optional[List[str]] = None


class AISummaryResponse(BaseModel):
    incident_id: str
    summary: str
    key_findings: List[str]
    timeline_highlights: List[str]
    identified_discrepancies: List[str]
    ai_provider: str
    model: str
    is_fallback: bool
    generated_at: datetime


# Full Comprehensive Incident Report
class IncidentReportResponse(BaseModel):
    incident: Dict[str, Any]
    evidence_inventory: List[Dict[str, Any]]
    vehicles_involved: List[Dict[str, Any]]
    timeline: Dict[str, Any]
    telemetry_analyses: List[Dict[str, Any]]
    contradictions: Dict[str, Any]
    investigation_summary: Dict[str, Any]
    report_generated_at: datetime
