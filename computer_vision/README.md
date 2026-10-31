# TRACE AI — Computer Vision Subsystem

The Computer Vision subsystem for **TRACE AI**, an AI-powered road accident investigation and kinematic reconstruction prototype.

---

## 1. Overview & Forensic Architecture

The subsystem provides automated vehicle detection, persistent multi-object tracking, image-plane kinematic analysis, candidate event extraction, and forensic video annotation from traffic surveillance, dashcam, and aerial crash footage.

### Technology Stack
- **Python 3.11+**
- **Ultralytics YOLOv8n**: Pretrained vehicular detector (cars, motorcycles, buses, trucks)
- **OpenCV**: Video container decoding, optical flow, frame-by-frame rendering, and video encoding
- **NumPy & Pandas**: IoU association matrix math and temporal vector analysis
- **Pydantic v2**: Strict schema validation for backend integration

---

## 2. Directory Structure

```
computer_vision/
  main.py                 # CLI execution entry point
  config.py               # Vehicle classes, confidence thresholds, and forensic parameters
  schemas.py              # Pydantic schemas matching the required JSON contract
  frame_extractor.py      # Video ingestion, format validation, timestamp preservation
  vehicle_detector.py     # Pretrained YOLOv8n inference with vehicular filtering
  object_tracker.py       # Persistent track assignment (CV-001, CV-002) and IoU matching
  motion_analyzer.py      # Image-plane displacement, velocity, and stopping state analysis
  event_extractor.py      # Candidate visual event extraction with epistemic classification
  visualization.py        # Video annotation (bounding boxes, track IDs, trails, and HUD)
  video_processor.py      # Master orchestrator uniting the end-to-end pipeline
  requirements.txt        # Python package dependencies
  README.md               # Architecture documentation
  tests/
    test_vision.py        # Automated test suite
```

---

## 3. Epistemic Classifications & Non-Negotiable Constraints

1. **Photogrammetric Distance Limitation**:
   *Without rigorous intrinsic/extrinsic camera calibration and ground survey control points, image-plane pixel movements are never converted into metric speeds (km/h) or physical distances (meters).* All visual kinematics report 2D pixel coordinates ($px$, $px/s$).
2. **Persistent Tracking IDs**:
   Tracks are assigned IDs `CV-001`, `CV-002`, etc. Appearance alone is never used to infer vehicle make or model (e.g. "Tesla" or "Ford").
3. **Collision Warning vs Proximity**:
   Bounding-box 2D overlap is classified as `VIDEO_INFERENCE` representing optical proximity or line-of-sight occlusion. It is never automatically declared a collision without physical CAN bus telemetry corroboration.

---

## 4. Structured JSON Output Schema

```json
{
  "video_metadata": {
    "fps": 30.0,
    "frame_count": 450,
    "duration_seconds": 15.0,
    "width": 1920,
    "height": 1080,
    "codec": "h264"
  },
  "tracks": [
    {
      "track_id": "CV-001",
      "class_name": "car",
      "apparent_direction": "DOWNWARD_APPROACH_RIGHTWARD",
      "apparent_state": "MOVING",
      "observations": [
        {
          "timestamp_seconds": 2.500,
          "frame_number": 75,
          "bbox": [100.0, 120.0, 300.0, 250.0],
          "confidence": 0.94,
          "center_point": [200.0, 185.0],
          "velocity_px_per_sec": [24.5, 48.2]
        }
      ]
    }
  ],
  "candidate_events": [
    {
      "event_id": "EVT-ENT-A8102",
      "event_type": "VEHICLE_ENTER_FRAME",
      "track_id": "CV-001",
      "timestamp_seconds": 2.500,
      "frame_number": 75,
      "description": "Track CV-001 (car) entered camera field of view at frame #75 (t=2.50s).",
      "classification": "VIDEO_OBSERVATION",
      "confidence": 0.94
    }
  ],
  "limitations": [
    "Forensic Restriction: In the absence of calibrated camera matrices, pixel movements cannot be converted to metric speed (km/h).",
    "Bounding-box overlap denotes visual proximity or occlusion, not confirmed physical collision."
  ],
  "evidence_id": "EVD-VID-01",
  "incident_id": "INC-20261030-DEMO1",
  "annotated_video_path": "cv_outputs/annotated_videos/annotated_EVD-VID-01_dashcam.mp4",
  "extracted_frame_paths": ["cv_outputs/extracted_frames/keyframe_EVD-VID-01_frame00000.jpg"],
  "processing_status": "COMPLETED"
}
```

---

## 5. Backend Integration Interface

The FastAPI backend invokes the computer vision engine via `video_processor.process_video_file`:

```python
from computer_vision.video_processor import video_processor

# Call from FastAPI route handler
result = video_processor.process_video_file(
    video_path=Path("/path/to/evidence.mp4"),
    evidence_id="EVD-20261030-01",
    incident_id="INC-20261030-01",
    sample_interval=2,
    generate_annotated_video=True,
)

# Convert result to timeline events or persist to database
metadata = result.video_metadata
tracks = result.tracks
events = result.candidate_events
annotated_path = result.annotated_video_path
```

---

## 6. Execution & Testing

### CLI Processing
```bash
python -m computer_vision.main --video /path/to/dashcam.mp4 --evidence_id EVD-001 --sample_interval 2
```

### Running Automated Test Suite
```bash
pytest computer_vision/tests/ -v
```
Verifies metadata parsing, timestamp preservation, vehicle detection coordinates, persistent ID tracking, trajectory analysis, candidate event extraction, and JSON contract conformance.
