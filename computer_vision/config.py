from pathlib import Path
from typing import Dict, List

# Target classes from standard COCO dataset for road vehicle investigation
TARGET_VEHICLE_CLASSES: Dict[int, str] = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# Model and inference defaults
DEFAULT_MODEL_NAME: str = "yolov8n.pt"
CONFIDENCE_THRESHOLD: float = 0.35
IOU_THRESHOLD: float = 0.45

# Tracking defaults
TRACKER_MAX_LOST_FRAMES: int = 25  # Frames to retain track before termination
TRACKER_IOU_MATCH_THRESHOLD: float = 0.3  # Minimum IoU for association
TRACK_ID_PREFIX: str = "CV-"  # Keep tracking IDs distinct from real vehicle names

# Motion analysis defaults
STOPPING_VELOCITY_THRESHOLD_PX: float = 2.0  # Pixels/sec considered stationary
SUDDEN_DELTA_VELOCITY_RATIO: float = 2.5     # Ratio spike indicating sharp trajectory shift

# Supported video extensions
SUPPORTED_VIDEO_EXTENSIONS: List[str] = [".mp4", ".mov", ".avi"]

# Output directory structure
BASE_OUTPUT_DIR: Path = Path("./cv_outputs")
ANNOTATED_VIDEOS_DIR: Path = BASE_OUTPUT_DIR / "annotated_videos"
EXTRACTED_FRAMES_DIR: Path = BASE_OUTPUT_DIR / "extracted_frames"
JSON_RESULTS_DIR: Path = BASE_OUTPUT_DIR / "json_results"

# Standard Forensic Limitation Disclaimer
FORENSIC_CAMERA_CALIBRATION_DISCLAIMER: str = (
    "Forensic Restriction: In the absence of calibrated intrinsic/extrinsic camera matrices and "
    "ground survey control points, image-plane pixel movements cannot be converted into metric "
    "speeds (km/h), physical distances (meters), or GPS coordinates. All visual kinematics reported "
    "here represent 2D image-plane coordinates only."
)
