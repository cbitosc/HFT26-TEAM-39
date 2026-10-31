import logging
from pathlib import Path
from typing import Dict, Any, Generator, Tuple, List, Optional
import cv2
import numpy as np

from computer_vision.config import SUPPORTED_VIDEO_EXTENSIONS
from computer_vision.schemas import VideoMetadata

logger = logging.getLogger(__name__)


class VideoIngestionError(Exception):
    pass


class FrameExtractor:
    """Safely ingests and extracts metadata and frames from video evidence files.
    
    Guarantees the original video file is strictly read-only and never altered.
    """

    def validate_file(self, video_path: Path) -> Path:
        """Validates existence and file extension of video file."""
        if not video_path.exists():
            raise VideoIngestionError(f"Video file not found at path: {video_path}")

        suffix = video_path.suffix.lower()
        if suffix not in SUPPORTED_VIDEO_EXTENSIONS:
            raise VideoIngestionError(
                f"Unsupported video extension '{suffix}'. Supported: {', '.join(SUPPORTED_VIDEO_EXTENSIONS)}"
            )

        return video_path

    def get_metadata(self, video_path: Path) -> VideoMetadata:
        """Extracts technical video properties using OpenCV."""
        self.validate_file(video_path)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise VideoIngestionError(f"Unable to open video stream from {video_path.name}. File may be corrupted.")

        try:
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            if fps <= 0 or np.isnan(fps):
                fps = 30.0  # Plausible default if container metadata missing

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)]).strip()

            duration_seconds = frame_count / fps if frame_count > 0 else 0.0

            return VideoMetadata(
                fps=round(fps, 3),
                frame_count=frame_count,
                duration_seconds=round(duration_seconds, 3),
                width=width,
                height=height,
                codec=codec or "unknown",
            )
        finally:
            cap.release()

    def iterate_frames(
        self,
        video_path: Path,
        sample_interval: int = 1,
    ) -> Generator[Tuple[int, float, np.ndarray], None, None]:
        """Yields (frame_number, timestamp_seconds, frame_bgr) at specified sample interval.
        
        Strictly preserves exact original video timestamps calculated as frame_idx / fps.
        """
        self.validate_file(video_path)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise VideoIngestionError(f"Cannot read video stream: {video_path.name}")

        fps = float(cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0 or np.isnan(fps):
            fps = 30.0

        frame_idx = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % sample_interval == 0:
                    # Calculate exact original timestamp in seconds
                    timestamp_sec = round(frame_idx / fps, 4)
                    yield (frame_idx, timestamp_sec, frame)

                frame_idx += 1
        finally:
            cap.release()

    def save_keyframe(
        self,
        frame: np.ndarray,
        output_path: Path,
    ) -> Path:
        """Saves a frame snapshot to disk without altering original content."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), frame)
        return output_path


# Global singleton
frame_extractor = FrameExtractor()
