from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    fps: float
    frame_count: int
    duration_seconds: float
    width: int
    height: int
    codec: Optional[str] = None


class DetectionBox(BaseModel):
    detection_id: str
    frame_number: int
    timestamp_seconds: float
    class_name: str
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2] bounding box in pixels")
    confidence: float


class TrackObservation(BaseModel):
    timestamp_seconds: float
    frame_number: int
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2] bounding box")
    confidence: float
    center_point: Optional[List[float]] = None
    velocity_px_per_sec: Optional[List[float]] = None


class TrackRecord(BaseModel):
    track_id: str = Field(..., description="Persistent tracking ID e.g. CV-001")
    class_name: str = Field(..., description="Detected vehicle type: car, motorcycle, bus, truck")
    observations: List[TrackObservation]
    apparent_direction: Optional[str] = None
    apparent_state: Optional[str] = None  # MOVING, STOPPED, DECELERATING


class CandidateEvent(BaseModel):
    event_id: str
    event_type: str  # VEHICLE_ENTER_FRAME, VEHICLE_EXIT_FRAME, APPARENT_STOPPING, SUDDEN_MOTION_CHANGE, PROXIMITY_OCCLUSION
    track_id: Optional[str] = None
    timestamp_seconds: float
    frame_number: int
    description: str
    classification: str = Field(..., description="VIDEO_OBSERVATION or VIDEO_INFERENCE")
    confidence: float


class VisionProcessingResult(BaseModel):
    video_metadata: VideoMetadata
    tracks: List[TrackRecord]
    candidate_events: List[CandidateEvent]
    limitations: List[str]
    # Backend integration fields
    evidence_id: Optional[str] = None
    incident_id: Optional[str] = None
    annotated_video_path: Optional[str] = None
    extracted_frame_paths: List[str] = Field(default_factory=list)
    processing_status: str = "COMPLETED"
