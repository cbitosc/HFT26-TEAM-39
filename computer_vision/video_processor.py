import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from computer_vision.config import (
    ANNOTATED_VIDEOS_DIR,
    EXTRACTED_FRAMES_DIR,
    JSON_RESULTS_DIR,
    FORENSIC_CAMERA_CALIBRATION_DISCLAIMER,
)
from computer_vision.frame_extractor import frame_extractor, VideoIngestionError
from computer_vision.vehicle_detector import vehicle_detector
from computer_vision.object_tracker import object_tracker
from computer_vision.motion_analyzer import motion_analyzer
from computer_vision.event_extractor import event_extractor
from computer_vision.visualization import video_annotator
from computer_vision.schemas import VisionProcessingResult

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Master orchestrator for the TRACE AI Computer Vision subsystem.
    
    Seamlessly integrates ingestion, detection, tracking, kinematic analysis,
    candidate event extraction, and visual annotation.
    """

    def process_video_file(
        self,
        video_path: Path,
        evidence_id: Optional[str] = None,
        incident_id: Optional[str] = None,
        sample_interval: int = 2,
        generate_annotated_video: bool = True,
        max_keyframes_to_save: int = 5,
    ) -> VisionProcessingResult:
        """Processes video file through the end-to-end computer vision pipeline."""
        video_path = Path(video_path)
        logger.info("Starting CV pipeline for video: %s (Evidence ID: %s)", video_path.name, evidence_id)

        # 1. Ingestion & Metadata Extraction
        metadata = frame_extractor.get_metadata(video_path)
        logger.info(
            "Video metadata: %dx%d @ %.2f fps, %d total frames (%.2fs)",
            metadata.width, metadata.height, metadata.fps, metadata.frame_count, metadata.duration_seconds
        )

        # 2. Reset tracker for new video stream
        object_tracker.reset()

        # 3. Detection and Tracking loop
        saved_keyframe_paths: List[str] = []
        keyframe_step = max(1, metadata.frame_count // max_keyframes_to_save) if metadata.frame_count > 0 else 30

        for frame_num, timestamp_sec, frame in frame_extractor.iterate_frames(
            video_path=video_path,
            sample_interval=sample_interval,
        ):
            # Detect vehicles
            detections = vehicle_detector.detect_frame(
                frame=frame,
                frame_number=frame_num,
                timestamp_seconds=timestamp_sec,
            )

            # Update tracks
            object_tracker.update(detections)

            # Save keyframe snapshot if at interval
            if len(saved_keyframe_paths) < max_keyframes_to_save and frame_num % keyframe_step == 0:
                kf_filename = f"keyframe_{evidence_id or 'vid'}_frame{frame_num:05d}.jpg"
                kf_path = EXTRACTED_FRAMES_DIR / kf_filename
                frame_extractor.save_keyframe(frame, kf_path)
                saved_keyframe_paths.append(str(kf_path))

        # 4. Finalize Tracks
        tracks = object_tracker.finalize_all_tracks()
        logger.info("Completed tracking. Isolated %d persistent vehicle track(s).", len(tracks))

        # 5. Motion Analysis across tracks
        for trk in tracks:
            motion_summary = motion_analyzer.analyze_track_motion(trk)
            logger.debug("Track %s motion summary: %s", trk.track_id, motion_summary)

        # 6. Extract Candidate Visual Kinematic Events
        candidate_events = event_extractor.extract_events(
            tracks=tracks,
            video_width=metadata.width,
            video_height=metadata.height,
            fps=metadata.fps,
        )
        logger.info("Extracted %d candidate visual event(s).", len(candidate_events))

        # 7. Render Annotated Video
        annotated_video_path = None
        if generate_annotated_video and metadata.frame_count > 0:
            out_filename = f"annotated_{evidence_id or 'cv'}_{video_path.stem}.mp4"
            out_path = ANNOTATED_VIDEOS_DIR / out_filename
            try:
                rendered_path = video_annotator.render_annotated_video(
                    input_video_path=video_path,
                    output_video_path=out_path,
                    tracks=tracks,
                    fps=metadata.fps,
                    width=metadata.width,
                    height=metadata.height,
                )
                annotated_video_path = str(rendered_path)
            except Exception as e:
                logger.error("Failed to render annotated video: %s", str(e))
                annotated_video_path = None

        # 8. Standard Forensic Limitations
        limitations = [
            FORENSIC_CAMERA_CALIBRATION_DISCLAIMER,
            "Bounding box tracking represents 2D image plane coordinates only.",
            "Vehicle classification (car, bus, truck, motorcycle) is derived from appearance features without VIN corroboration.",
            "Overlapping bounding boxes denote spatial proximity or visual occlusion, not confirmed physical collision.",
        ]

        if not tracks:
            limitations.append("Notice: Zero persistent vehicle tracks were isolated above confidence thresholds.")

        result = VisionProcessingResult(
            video_metadata=metadata,
            tracks=tracks,
            candidate_events=candidate_events,
            limitations=limitations,
            evidence_id=evidence_id,
            incident_id=incident_id,
            annotated_video_path=annotated_video_path,
            extracted_frame_paths=saved_keyframe_paths,
            processing_status="COMPLETED",
        )

        # Save structured JSON output
        JSON_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        json_path = JSON_RESULTS_DIR / f"cv_results_{evidence_id or video_path.stem}.json"
        with open(json_path, "w", encoding="utf-8") as f_json:
            f_json.write(result.model_dump_json(indent=2))

        logger.info("Saved structured CV output to %s", json_path)
        return result


# Global singleton
video_processor = VideoProcessor()
