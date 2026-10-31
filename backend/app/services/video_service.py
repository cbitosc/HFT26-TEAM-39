import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Try to import advanced computer_vision subsystem
try:
    from computer_vision.video_processor import video_processor
    HAS_CV_SUBSYSTEM = True
except ImportError:
    video_processor = None
    HAS_CV_SUBSYSTEM = False


class ComputerVisionService:
    """Dedicated service interface for computer vision algorithms and video analysis.
    
    Provides structured vehicle detection, motion tracking, optical flow analysis,
    and impact detection from crash footage.
    """

    def analyze_video(
        self,
        video_path: Path,
        sample_rate_frames: int = 5,
        evidence_id: Optional[str] = None,
        incident_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Processes video file using OpenCV and extracts structured kinematics & visual detections."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file does not exist: {video_path}")

        # If computer_vision subsystem is active, run comprehensive detection and tracking pipeline
        if HAS_CV_SUBSYSTEM and video_processor is not None:
            try:
                cv_res = video_processor.process_video_file(
                    video_path=video_path,
                    evidence_id=evidence_id,
                    incident_id=incident_id,
                    sample_interval=sample_rate_frames,
                    generate_annotated_video=True,
                )
                formatted_events = [
                    {
                        "frame_number": e.frame_number,
                        "timestamp_offset_seconds": e.timestamp_seconds,
                        "event_type": e.event_type,
                        "description": e.description,
                        "motion_magnitude": 1.0,
                        "confidence": e.confidence,
                        "bounding_boxes": [],
                    }
                    for e in cv_res.candidate_events
                ]
                return {
                    "frame_count": cv_res.video_metadata.frame_count,
                    "fps": cv_res.video_metadata.fps,
                    "duration_seconds": cv_res.video_metadata.duration_seconds,
                    "resolution": f"{cv_res.video_metadata.width}x{cv_res.video_metadata.height}",
                    "events_detected": formatted_events,
                    "tracks": [t.dict() for t in cv_res.tracks],
                    "annotated_video_path": cv_res.annotated_video_path,
                    "extracted_frames": cv_res.extracted_frame_paths,
                    "limitations": cv_res.limitations,
                    "cv_engine_notes": f"Analyzed {cv_res.video_metadata.frame_count} frames. Tracked {len(cv_res.tracks)} vehicle entities.",
                }
            except Exception as e:
                logger.warning("computer_vision subsystem failed, falling back to direct OpenCV: %s", str(e))

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"OpenCV could not open video file: {video_path.name}")

        try:
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            if fps <= 0 or np.isnan(fps):
                fps = 30.0  # Fallback default standard frame rate

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration_seconds = frame_count / fps if frame_count > 0 else 0.0

            events: List[Dict[str, Any]] = []
            prev_gray = None
            frame_idx = 0
            motion_magnitudes = []

            # Background subtractor for vehicle contour detection
            bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=50, varThreshold=25, detectShadows=False)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % sample_rate_frames == 0:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    timestamp_offset = frame_idx / fps

                    # 1. Optical Flow & Motion Intensity
                    magnitude = 0.0
                    if prev_gray is not None and prev_gray.shape == gray.shape:
                        # Farneback dense optical flow
                        flow = cv2.calcOpticalFlowFarneback(
                            prev_gray,
                            gray,
                            None,
                            pyr_scale=0.5,
                            levels=3,
                            winsize=15,
                            iterations=2,
                            poly_n=5,
                            poly_sigma=1.1,
                            flags=0,
                        )
                        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                        magnitude = float(np.mean(mag))
                        motion_magnitudes.append((frame_idx, timestamp_offset, magnitude))

                    # 2. Vehicle candidate bounding boxes via background subtraction
                    fg_mask = bg_subtractor.apply(frame)
                    # Morphological cleanup
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
                    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    detected_boxes = []
                    min_area = (width * height) * 0.005  # minimum vehicle size
                    for cnt in contours:
                        if cv2.contourArea(cnt) > min_area:
                            x, y, w, h = cv2.boundingRect(cnt)
                            detected_boxes.append({
                                "x": int(x),
                                "y": int(y),
                                "width": int(w),
                                "height": int(h),
                                "area": int(w * h),
                            })

                    # If significant motion or objects detected
                    if detected_boxes and magnitude > 1.0:
                        events.append({
                            "frame_number": frame_idx,
                            "timestamp_offset_seconds": round(timestamp_offset, 3),
                            "event_type": "VEHICLE_MOTION_TRACKING",
                            "description": f"Visual tracking active. {len(detected_boxes)} candidate vehicle contour(s) tracked. Mean optical flow magnitude: {magnitude:.2f} px/frame.",
                            "motion_magnitude": round(magnitude, 3),
                            "confidence": min(0.95, round(0.6 + (len(detected_boxes) * 0.1), 2)),
                            "bounding_boxes": detected_boxes[:5],
                        })

                    prev_gray = gray

                frame_idx += 1

            # 3. Detect sudden deceleration / visual impact peak
            if motion_magnitudes:
                mags = [m[2] for m in motion_magnitudes]
                mean_mag = np.mean(mags)
                std_mag = np.std(mags)

                for f_idx, t_offset, mag in motion_magnitudes:
                    if mag > mean_mag + (2.0 * std_mag) and mag > 2.5:
                        events.append({
                            "frame_number": f_idx,
                            "timestamp_offset_seconds": round(t_offset, 3),
                            "event_type": "ANOMALOUS_MOTION_SPIKE",
                            "description": f"Rapid visual motion change / potential impact at offset +{t_offset:.2f}s (flow magnitude: {mag:.2f} vs avg {mean_mag:.2f}).",
                            "motion_magnitude": round(mag, 3),
                            "confidence": 0.88,
                            "bounding_boxes": [],
                        })

            return {
                "frame_count": frame_count,
                "fps": round(fps, 2),
                "duration_seconds": round(duration_seconds, 2),
                "resolution": f"{width}x{height}",
                "events_detected": events,
                "cv_engine_notes": (
                    f"Analyzed {frame_count} frames at {fps:.1f} fps across {duration_seconds:.2f}s duration. "
                    f"Identified {len(events)} visual kinematic events."
                ),
            }

        finally:
            cap.release()


# Global singleton
video_service = ComputerVisionService()
