import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from computer_vision.config import STOPPING_VELOCITY_THRESHOLD_PX
from computer_vision.schemas import TrackRecord

logger = logging.getLogger(__name__)


class MotionAnalyzer:
    """Analyzes image-plane trajectory vectors for tracked vehicles.
    
    STRICT FORENSIC RULE:
    Pixel movement on the 2D sensor image plane is NEVER converted into real-world
    physical velocity (km/h) or metric distances (meters) without rigorous camera
    calibration and extrinsic ground survey benchmarks.
    """

    def analyze_track_motion(self, track: TrackRecord) -> Dict[str, Any]:
        """Calculates 2D image-plane displacement, velocity, apparent direction, and state transitions."""
        obs = track.observations
        if len(obs) < 2:
            return {
                "apparent_direction": "INSUFFICIENT_OBSERVATIONS",
                "total_image_plane_displacement_px": 0.0,
                "apparent_state": "UNKNOWN",
                "detection_gap_count": 0,
                "track_duration_seconds": 0.0,
            }

        start_obs = obs[0]
        end_obs = obs[-1]
        track_duration = round(end_obs.timestamp_seconds - start_obs.timestamp_seconds, 3)

        # Calculate total image-plane net vector
        start_c = start_obs.center_point or [(start_obs.bbox[0] + start_obs.bbox[2])/2, (start_obs.bbox[1] + start_obs.bbox[3])/2]
        end_c = end_obs.center_point or [(end_obs.bbox[0] + end_obs.bbox[2])/2, (end_obs.bbox[1] + end_obs.bbox[3])/2]

        dx = end_c[0] - start_c[0]
        dy = end_c[1] - start_c[1]
        total_displacement = round(float(np.sqrt(dx**2 + dy**2)), 2)

        # Determine dominant direction in image plane (x: lateral, y: longitudinal/approach)
        direction_parts = []
        if abs(dy) > 10.0:
            direction_parts.append("DOWNWARD_APPROACH" if dy > 0 else "UPWARD_RECEDING")
        if abs(dx) > 10.0:
            direction_parts.append("RIGHTWARD" if dx > 0 else "LEFTWARD")

        direction_label = "_".join(direction_parts) if direction_parts else "APPROXIMATELY_STATIONARY"

        # Check for apparent stopping or deceleration in image plane
        velocities = []
        for o in obs:
            if o.velocity_px_per_sec:
                v_mag = np.sqrt(o.velocity_px_per_sec[0]**2 + o.velocity_px_per_sec[1]**2)
                velocities.append(float(v_mag))

        mean_v = float(np.mean(velocities)) if velocities else 0.0
        final_v = float(np.mean(velocities[-3:])) if len(velocities) >= 3 else mean_v

        apparent_state = "MOVING"
        if final_v < STOPPING_VELOCITY_THRESHOLD_PX:
            apparent_state = "APPARENT_STOP"
        elif mean_v > 0 and (final_v / mean_v) < 0.35:
            apparent_state = "DECELERATING"

        # Check frame gaps
        frame_diffs = [obs[i+1].frame_number - obs[i].frame_number for i in range(len(obs)-1)]
        detection_gaps = sum(1 for diff in frame_diffs if diff > 5)

        track.apparent_direction = direction_label
        track.apparent_state = apparent_state

        return {
            "apparent_direction": direction_label,
            "total_image_plane_displacement_px": total_displacement,
            "net_dx_px": round(dx, 2),
            "net_dy_px": round(dy, 2),
            "mean_image_plane_velocity_px_per_sec": round(mean_v, 2),
            "apparent_state": apparent_state,
            "detection_gap_count": detection_gaps,
            "track_duration_seconds": track_duration,
            "total_frames_tracked": end_obs.frame_number - start_obs.frame_number + 1,
        }


# Global singleton
motion_analyzer = MotionAnalyzer()
