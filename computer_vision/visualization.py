import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import cv2
import numpy as np

from computer_vision.schemas import TrackRecord

logger = logging.getLogger(__name__)

# Consistent palette for tracked objects
TRACK_COLORS = [
    (230, 92, 0),    # Cyan/Blue
    (0, 153, 255),   # Orange
    (76, 175, 80),   # Green
    (156, 39, 176),  # Purple
    (244, 67, 54),   # Red
    (255, 235, 59),  # Yellow
]


class VideoAnnotator:
    """Generates professional, forensic-grade annotated video and keyframe snapshots.
    
    Draws tracking ID labels, detection confidences, trajectory trails, and timestamp overlays.
    Preserves original video files completely untouched.
    """

    def render_annotated_video(
        self,
        input_video_path: Path,
        output_video_path: Path,
        tracks: List[TrackRecord],
        fps: float,
        width: int,
        height: int,
        max_trail_points: int = 25,
    ) -> Path:
        """Draws bounding boxes, persistent track IDs, and center trails on video frames."""
        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        # Index track observations by frame number
        # frame_number -> list of (track_id, class_name, bbox, confidence, center_point)
        obs_by_frame: Dict[int, List[Dict[str, Any]]] = {}
        # track_id -> list of all past center points up to current frame
        trail_history: Dict[str, List[Tuple[int, int]]] = {}

        for trk in tracks:
            trail_history[trk.track_id] = []
            for o in trk.observations:
                if o.frame_number not in obs_by_frame:
                    obs_by_frame[o.frame_number] = []
                obs_by_frame[o.frame_number].append({
                    "track_id": trk.track_id,
                    "class_name": trk.class_name,
                    "bbox": o.bbox,
                    "confidence": o.confidence,
                    "center_point": o.center_point,
                })

        cap = cv2.VideoCapture(str(input_video_path))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))

        frame_idx = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                timestamp_sec = frame_idx / fps

                # Draw any tracks active on this frame
                if frame_idx in obs_by_frame:
                    for item in obs_by_frame[frame_idx]:
                        t_id = item["track_id"]
                        cls_name = item["class_name"]
                        x1, y1, x2, y2 = [int(v) for v in item["bbox"]]
                        conf = item["confidence"]

                        # Pick color deterministically based on track ID number
                        color_idx = int("".join(filter(str.isdigit, t_id)) or "0") % len(TRACK_COLORS)
                        color = TRACK_COLORS[color_idx]

                        # 1. Draw Bounding Box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                        # 2. Draw Label Banner [CV-001 | car (0.92)]
                        label = f"{t_id} | {cls_name} ({conf:.2f})"
                        (lbl_w, lbl_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                        top_y = max(y1, lbl_h + 6)
                        cv2.rectangle(frame, (x1, top_y - lbl_h - 6), (x1 + lbl_w + 6, top_y), color, -1)
                        cv2.putText(frame, label, (x1 + 3, top_y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

                        # 3. Update & Draw Trajectory Trail
                        if item["center_point"]:
                            cx, cy = int(item["center_point"][0]), int(item["center_point"][1])
                            trail_history[t_id].append((cx, cy))
                            if len(trail_history[t_id]) > max_trail_points:
                                trail_history[t_id].pop(0)

                            pts = trail_history[t_id]
                            for p_i in range(1, len(pts)):
                                alpha = p_i / len(pts)
                                thickness = max(1, int(alpha * 3))
                                cv2.line(frame, pts[p_i - 1], pts[p_i], color, thickness, cv2.LINE_AA)

                # 4. Global Forensic Telemetry Watermark & Timestamp
                hud_text = f"TRACE AI CV ENGINE | FRAME #{frame_idx:05d} | T+{timestamp_sec:.2f}s"
                cv2.rectangle(frame, (10, 10), (380, 34), (15, 23, 42), -1)
                cv2.putText(frame, hud_text, (18, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

                writer.write(frame)
                frame_idx += 1
        finally:
            cap.release()
            writer.release()

        logger.info("Rendered annotated video with %d frames to %s", frame_idx, output_video_path)
        return output_video_path

    def save_annotated_frame(
        self,
        frame: np.ndarray,
        output_path: Path,
        detections: List[Dict[str, Any]],
        timestamp_sec: float,
        frame_idx: int,
    ) -> Path:
        """Annotates and writes a single high-resolution keyframe image."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        annotated = frame.copy()

        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det.get("bbox", [0, 0, 0, 0])]
            t_id = det.get("track_id", "CV-DET")
            cls_name = det.get("class_name", "vehicle")
            conf = det.get("confidence", 1.0)

            color = (230, 92, 0)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label = f"{t_id} | {cls_name} ({conf:.2f})"
            cv2.putText(annotated, label, (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        hud_text = f"TRACE AI KEYFRAME | FRAME #{frame_idx:05d} | T+{timestamp_sec:.2f}s"
        cv2.putText(annotated, hud_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imwrite(str(output_path), annotated)
        return output_path


# Global singleton
video_annotator = VideoAnnotator()
