import logging
import uuid
from typing import List, Dict, Any, Tuple
import numpy as np

from computer_vision.config import SUDDEN_DELTA_VELOCITY_RATIO
from computer_vision.schemas import CandidateEvent, TrackRecord
from computer_vision.object_tracker import compute_iou

logger = logging.getLogger(__name__)


class EventExtractor:
    """Extracts candidate visual kinematic events from tracked vehicle trajectories.
    
    Categorizes events under strict epistemic standards:
    - VIDEO_OBSERVATION: Direct perceptual facts (entry, exit, visual stop).
    - VIDEO_INFERENCE: Hypothesized transitions (sharp trajectory shift, proximity overlap).
    
    CRITICAL FORENSIC RULE:
    Bounding-box overlap is NEVER classified as an automatic collision. In 2D monocular
    projections, occlusion and parallax frequently cause overlapping bounding boxes
    without physical contact.
    """

    def extract_events(
        self,
        tracks: List[TrackRecord],
        video_width: int,
        video_height: int,
        fps: float,
    ) -> List[CandidateEvent]:
        """Scans tracks for entry, exit, stopping, trajectory changes, and proximity overlaps."""
        events: List[CandidateEvent] = []

        # 1. Individual Track Events
        for track in tracks:
            obs = track.observations
            if len(obs) < 2:
                continue

            first_obs = obs[0]
            last_obs = obs[-1]

            # Vehicle Entering Frame (VIDEO_OBSERVATION)
            # Only trigger if track begins after initial start of video (e.g. frame > 5)
            if first_obs.frame_number > 5:
                events.append(
                    CandidateEvent(
                        event_id=f"EVT-ENT-{uuid.uuid4().hex[:6].upper()}",
                        event_type="VEHICLE_ENTER_FRAME",
                        track_id=track.track_id,
                        timestamp_seconds=first_obs.timestamp_seconds,
                        frame_number=first_obs.frame_number,
                        description=(
                            f"Track {track.track_id} ({track.class_name}) entered camera field of view "
                            f"at frame #{first_obs.frame_number} (t={first_obs.timestamp_seconds:.2f}s)."
                        ),
                        classification="VIDEO_OBSERVATION",
                        confidence=first_obs.confidence,
                    )
                )

            # Check for sudden image-plane movement change (VIDEO_INFERENCE)
            velocities = [
                np.sqrt(o.velocity_px_per_sec[0]**2 + o.velocity_px_per_sec[1]**2)
                for o in obs
                if o.velocity_px_per_sec
            ]

            if len(velocities) >= 5:
                mean_v = float(np.mean(velocities))
                for i in range(1, len(velocities)):
                    delta_v = abs(velocities[i] - velocities[i - 1])
                    if mean_v > 5.0 and (delta_v / mean_v) > SUDDEN_DELTA_VELOCITY_RATIO:
                        target_obs = obs[i]
                        events.append(
                            CandidateEvent(
                                event_id=f"EVT-SUD-{uuid.uuid4().hex[:6].upper()}",
                                event_type="SUDDEN_IMAGE_PLANE_MOTION_CHANGE",
                                track_id=track.track_id,
                                timestamp_seconds=target_obs.timestamp_seconds,
                                frame_number=target_obs.frame_number,
                                description=(
                                    f"Track {track.track_id} exhibited a sudden velocity discontinuity on the image plane "
                                    f"at t={target_obs.timestamp_seconds:.2f}s (delta: {delta_v:.1f} px/s). Potential kinematic perturbation."
                                ),
                                classification="VIDEO_INFERENCE",
                                confidence=0.85,
                            )
                        )
                        break  # Report only primary significant shift per track

            # Apparent Stopping (VIDEO_OBSERVATION)
            if track.apparent_state == "APPARENT_STOP" and len(obs) >= 6:
                # Find the transition frame where velocity dropped below threshold
                stop_obs = obs[-1]
                events.append(
                    CandidateEvent(
                        event_id=f"EVT-STP-{uuid.uuid4().hex[:6].upper()}",
                        event_type="APPARENT_STOPPING",
                        track_id=track.track_id,
                        timestamp_seconds=stop_obs.timestamp_seconds,
                        frame_number=stop_obs.frame_number,
                        description=(
                            f"Track {track.track_id} came to an apparent visual stop on the image plane "
                            f"at t={stop_obs.timestamp_seconds:.2f}s."
                        ),
                        classification="VIDEO_OBSERVATION",
                        confidence=0.92,
                    )
                )

        # 2. Inter-Vehicle Proximity and Occlusion Analysis (VIDEO_INFERENCE)
        # Scan for simultaneous frames where tracks overlap or come into close proximity
        if len(tracks) >= 2:
            events.extend(self._detect_inter_vehicle_proximity(tracks))

        # Sort all candidate events chronologically
        events.sort(key=lambda e: e.timestamp_seconds)
        return events

    def _detect_inter_vehicle_proximity(self, tracks: List[TrackRecord]) -> List[CandidateEvent]:
        """Identifies bounding box overlap or close proximity between pairs of vehicles."""
        proximity_events: List[CandidateEvent] = []

        # Index observations by frame_number
        track_obs_by_frame: Dict[str, Dict[int, Any]] = {}
        for t in tracks:
            track_obs_by_frame[t.track_id] = {o.frame_number: o for o in t.observations}

        track_ids = list(track_obs_by_frame.keys())
        for i in range(len(track_ids)):
            for j in range(i + 1, len(track_ids)):
                t1_id = track_ids[i]
                t2_id = track_ids[j]

                # Find common frames
                frames1 = set(track_obs_by_frame[t1_id].keys())
                frames2 = set(track_obs_by_frame[t2_id].keys())
                common_frames = sorted(list(frames1.intersection(frames2)))

                max_iou = 0.0
                critical_frame = None

                for f in common_frames:
                    box1 = track_obs_by_frame[t1_id][f].bbox
                    box2 = track_obs_by_frame[t2_id][f].bbox
                    iou = compute_iou(box1, box2)
                    if iou > max_iou:
                        max_iou = iou
                        critical_frame = f

                # If significant 2D overlap occurred
                if max_iou > 0.15 and critical_frame is not None:
                    crit_obs = track_obs_by_frame[t1_id][critical_frame]
                    proximity_events.append(
                        CandidateEvent(
                            event_id=f"EVT-OVR-{uuid.uuid4().hex[:6].upper()}",
                            event_type="VEHICLE_PROXIMITY_OCCLUSION",
                            track_id=f"{t1_id}+{t2_id}",
                            timestamp_seconds=crit_obs.timestamp_seconds,
                            frame_number=critical_frame,
                            description=(
                                f"Bounding-box 2D overlap (IoU: {max_iou:.2f}) observed between {t1_id} and {t2_id} "
                                f"at t={crit_obs.timestamp_seconds:.2f}s. "
                                f"FORENSIC CAUTION: Indicates proximity or visual occlusion; does NOT constitute conclusive collision proof without CAN bus impact confirmation."
                            ),
                            classification="VIDEO_INFERENCE",
                            confidence=round(min(0.95, 0.6 + max_iou), 2),
                        )
                    )

        return proximity_events


# Global singleton
event_extractor = EventExtractor()
