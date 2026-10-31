import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from computer_vision.config import (
    TRACKER_MAX_LOST_FRAMES,
    TRACKER_IOU_MATCH_THRESHOLD,
    TRACK_ID_PREFIX,
)
from computer_vision.schemas import DetectionBox, TrackObservation, TrackRecord

logger = logging.getLogger(__name__)


def compute_iou(boxA: List[float], boxB: List[float]) -> float:
    """Computes Intersection over Union (IoU) between two [x1, y1, x2, y2] boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interWidth = max(0.0, xB - xA)
    interHeight = max(0.0, yB - yA)
    interArea = interWidth * interHeight

    boxAArea = max(0.0, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    boxBArea = max(0.0, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

    denom = boxAArea + boxBArea - interArea
    if denom <= 0:
        return 0.0

    return interArea / denom


class VehicleTrack:
    """Internal track state representation for an isolated visual entity."""

    def __init__(self, track_number: int, initial_detection: DetectionBox):
        self.track_id = f"{TRACK_ID_PREFIX}{track_number:03d}"
        self.class_name = initial_detection.class_name
        self.last_bbox = initial_detection.bbox
        self.last_frame = initial_detection.frame_number
        self.lost_frames = 0
        self.observations: List[TrackObservation] = []

        self.add_observation(initial_detection)

    def add_observation(self, det: DetectionBox):
        """Appends a new observation and computes center point and velocity."""
        cx = (det.bbox[0] + det.bbox[2]) / 2.0
        cy = (det.bbox[1] + det.bbox[3]) / 2.0
        velocity = None

        if self.observations:
            prev = self.observations[-1]
            dt = det.timestamp_seconds - prev.timestamp_seconds
            if dt > 0 and prev.center_point:
                vx = (cx - prev.center_point[0]) / dt
                vy = (cy - prev.center_point[1]) / dt
                velocity = [round(vx, 2), round(vy, 2)]

        obs = TrackObservation(
            timestamp_seconds=det.timestamp_seconds,
            frame_number=det.frame_number,
            bbox=det.bbox,
            confidence=det.confidence,
            center_point=[round(cx, 2), round(cy, 2)],
            velocity_px_per_sec=velocity,
        )

        self.observations.append(obs)
        self.last_bbox = det.bbox
        self.last_frame = det.frame_number
        self.lost_frames = 0


class ObjectTracker:
    """Persistent object tracker using IoU and spatial proximity matching.
    
    Assigns sequential CV-001, CV-002 IDs and maintains tracks across temporary occlusions.
    """

    def __init__(
        self,
        max_lost_frames: int = TRACKER_MAX_LOST_FRAMES,
        iou_threshold: float = TRACKER_IOU_MATCH_THRESHOLD,
    ):
        self.max_lost_frames = max_lost_frames
        self.iou_threshold = iou_threshold
        self.track_counter = 1
        self.active_tracks: List[VehicleTrack] = []
        self.finished_tracks: List[VehicleTrack] = []

    def reset(self):
        """Resets tracker state."""
        self.track_counter = 1
        self.active_tracks = []
        self.finished_tracks = []

    def update(self, detections: List[DetectionBox]) -> List[VehicleTrack]:
        """Associates detections with active tracks or creates new persistent tracks."""
        if not self.active_tracks:
            for det in detections:
                new_track = VehicleTrack(self.track_counter, det)
                self.track_counter += 1
                self.active_tracks.append(new_track)
            return self.active_tracks

        # Compute pairwise IoU matrix
        num_tracks = len(self.active_tracks)
        num_dets = len(detections)

        iou_matrix = np.zeros((num_tracks, num_dets), dtype=float)
        for t_idx, track in enumerate(self.active_tracks):
            for d_idx, det in enumerate(detections):
                # Prefer same class association
                score = compute_iou(track.last_bbox, det.bbox)
                if track.class_name == det.class_name:
                    score += 0.05
                iou_matrix[t_idx, d_idx] = score

        # Greedy matching by maximum IoU
        matched_tracks = set()
        matched_dets = set()

        # Sort all (t, d) pairs by descending score
        if num_tracks > 0 and num_dets > 0:
            indices = np.unravel_index(np.argsort(-iou_matrix, axis=None), iou_matrix.shape)
            for t_idx, d_idx in zip(indices[0], indices[1]):
                if t_idx in matched_tracks or d_idx in matched_dets:
                    continue
                if iou_matrix[t_idx, d_idx] >= self.iou_threshold:
                    self.active_tracks[t_idx].add_observation(detections[d_idx])
                    matched_tracks.add(t_idx)
                    matched_dets.add(d_idx)

        # Increment lost frames for unmatched active tracks
        still_active = []
        for t_idx, track in enumerate(self.active_tracks):
            if t_idx not in matched_tracks:
                track.lost_frames += 1
                if track.lost_frames <= self.max_lost_frames:
                    still_active.append(track)
                else:
                    self.finished_tracks.append(track)
            else:
                still_active.append(track)

        self.active_tracks = still_active

        # Create new tracks for unmatched detections
        for d_idx, det in enumerate(detections):
            if d_idx not in matched_dets:
                new_track = VehicleTrack(self.track_counter, det)
                self.track_counter += 1
                self.active_tracks.append(new_track)

        return self.active_tracks

    def finalize_all_tracks(self) -> List[TrackRecord]:
        """Combines and returns all finished and remaining active tracks as TrackRecords."""
        all_tracks = self.finished_tracks + self.active_tracks
        records: List[TrackRecord] = []

        for trk in all_tracks:
            # Filter out tiny spurious tracks (noise with < 2 observations)
            if len(trk.observations) >= 2:
                records.append(
                    TrackRecord(
                        track_id=trk.track_id,
                        class_name=trk.class_name,
                        observations=trk.observations,
                    )
                )

        # Sort by track ID (CV-001, CV-002)
        records.sort(key=lambda x: x.track_id)
        return records


# Global singleton
object_tracker = ObjectTracker()
