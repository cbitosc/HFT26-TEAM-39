import os
import shutil
import pytest
from pathlib import Path
import numpy as np
import cv2

from computer_vision.config import BASE_OUTPUT_DIR
from computer_vision.frame_extractor import frame_extractor, VideoIngestionError
from computer_vision.vehicle_detector import vehicle_detector
from computer_vision.object_tracker import object_tracker
from computer_vision.motion_analyzer import motion_analyzer
from computer_vision.event_extractor import event_extractor
from computer_vision.video_processor import video_processor
from computer_vision.schemas import DetectionBox


@pytest.fixture(scope="module")
def sample_video_path(tmp_path_factory) -> Path:
    """Generates a synthetic 20-frame MP4 video containing moving vehicle shapes."""
    temp_dir = tmp_path_factory.mktemp("test_cv_video")
    video_file = temp_dir / "sample_traffic_test.mp4"

    width, height = 320, 240
    fps = 10.0
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_file), fourcc, fps, (width, height))

    # Frame 0 to 19: generate two moving vehicle-like rectangles
    for i in range(20):
        frame = np.full((height, width, 3), 40, dtype=np.uint8)

        # Road surface
        cv2.rectangle(frame, (0, 80), (width, 180), (60, 60, 60), -1)
        # Lane divider
        cv2.line(frame, (0, 130), (width, 130), (255, 255, 255), 1)

        # Vehicle 1 moving left to right
        v1_x = int(20 + i * 8)
        cv2.rectangle(frame, (v1_x, 90), (v1_x + 35, 120), (220, 180, 50), -1)

        # Vehicle 2 moving right to left
        v2_x = int(240 - i * 6)
        cv2.rectangle(frame, (v2_x, 140), (v2_x + 40, 170), (50, 50, 200), -1)

        out.write(frame)

    out.release()
    yield video_file


def test_frame_extractor_metadata(sample_video_path):
    """Verifies video format validation and metadata extraction."""
    meta = frame_extractor.get_metadata(sample_video_path)
    assert meta.frame_count == 20
    assert meta.fps == 10.0
    assert meta.duration_seconds == 2.0
    assert meta.width == 320
    assert meta.height == 240


def test_frame_extractor_timestamps(sample_video_path):
    """Verifies that frame timestamps are strictly preserved as frame_idx / fps."""
    frames = list(frame_extractor.iterate_frames(sample_video_path, sample_interval=2))
    assert len(frames) == 10  # 20 frames sampled at step 2

    # Check first frame (idx 0 -> 0.0s) and second frame (idx 2 -> 0.2s)
    assert frames[0][0] == 0
    assert frames[0][1] == 0.0
    assert frames[1][0] == 2
    assert frames[1][1] == 0.2


def test_invalid_video_format(tmp_path):
    """Verifies that unsupported or missing files raise VideoIngestionError."""
    fake_file = tmp_path / "document.pdf"
    fake_file.write_text("not a video")
    with pytest.raises(VideoIngestionError):
        frame_extractor.get_metadata(fake_file)


def test_vehicle_detection_and_coordinates(sample_video_path):
    """Verifies vehicle detector returns valid bounding boxes with coordinates."""
    cap = cv2.VideoCapture(str(sample_video_path))
    ret, frame = cap.read()
    cap.release()
    assert ret is True

    dets = vehicle_detector.detect_frame(frame, frame_number=0, timestamp_seconds=0.0)
    assert isinstance(dets, list)
    for d in dets:
        assert isinstance(d, DetectionBox)
        assert len(d.bbox) == 4
        assert d.bbox[0] < d.bbox[2]  # x1 < x2
        assert d.bbox[1] < d.bbox[3]  # y1 < y2
        assert 0.0 <= d.confidence <= 1.0


def test_object_tracker_persistent_ids():
    """Verifies object tracker assigns persistent CV-001 IDs across consecutive frames."""
    object_tracker.reset()

    # Frame 0: 2 vehicles detected
    det1 = DetectionBox(detection_id="D1", frame_number=0, timestamp_seconds=0.0, class_name="car", bbox=[20, 90, 55, 120], confidence=0.9)
    det2 = DetectionBox(detection_id="D2", frame_number=0, timestamp_seconds=0.0, class_name="car", bbox=[200, 140, 240, 170], confidence=0.88)
    tracks_f0 = object_tracker.update([det1, det2])
    assert len(tracks_f0) == 2
    assert tracks_f0[0].track_id == "CV-001"
    assert tracks_f0[1].track_id == "CV-002"

    # Frame 1: moved slightly
    det1_next = DetectionBox(detection_id="D3", frame_number=1, timestamp_seconds=0.1, class_name="car", bbox=[28, 90, 63, 120], confidence=0.91)
    det2_next = DetectionBox(detection_id="D4", frame_number=1, timestamp_seconds=0.1, class_name="car", bbox=[194, 140, 234, 170], confidence=0.89)
    tracks_f1 = object_tracker.update([det1_next, det2_next])

    # IDs should persist without duplicates
    assert tracks_f1[0].track_id == "CV-001"
    assert tracks_f1[1].track_id == "CV-002"

    all_records = object_tracker.finalize_all_tracks()
    assert len(all_records) == 2
    assert all_records[0].track_id == "CV-001"
    assert len(all_records[0].observations) == 2


def test_motion_analyzer_image_plane_constraint():
    """Verifies that motion analyzer calculates image-plane displacement without metric conversion."""
    object_tracker.reset()
    det_a = DetectionBox(detection_id="D1", frame_number=0, timestamp_seconds=0.0, class_name="car", bbox=[0, 0, 50, 50], confidence=0.9)
    det_b = DetectionBox(detection_id="D2", frame_number=10, timestamp_seconds=1.0, class_name="car", bbox=[100, 0, 150, 50], confidence=0.9)

    object_tracker.update([det_a])
    object_tracker.update([det_b])
    records = object_tracker.finalize_all_tracks()

    summary = motion_analyzer.analyze_track_motion(records[0])
    assert summary["total_image_plane_displacement_px"] > 0
    assert "RIGHTWARD" in summary["apparent_direction"]


def test_full_pipeline_orchestrator(sample_video_path):
    """Verifies full end-to-end processing pipeline outputting valid JSON and annotated media."""
    result = video_processor.process_video_file(
        video_path=sample_video_path,
        evidence_id="EVD-TEST-01",
        incident_id="INC-TEST-01",
        sample_interval=1,
        generate_annotated_video=True,
    )

    # Schema verification
    assert result.video_metadata.frame_count == 20
    assert result.evidence_id == "EVD-TEST-01"
    assert result.incident_id == "INC-TEST-01"
    assert isinstance(result.tracks, list)
    assert isinstance(result.candidate_events, list)
    assert len(result.limitations) >= 3

    # Check limitation notice exists
    assert any("calibration" in lim.lower() for lim in result.limitations)

    # Check annotated video file was created
    if result.annotated_video_path:
        assert Path(result.annotated_video_path).exists()
