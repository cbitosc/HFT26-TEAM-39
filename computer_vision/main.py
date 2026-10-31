import argparse
import json
import logging
import sys
from pathlib import Path

from computer_vision.video_processor import video_processor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("TRACE_AI_CV")


def main():
    parser = argparse.ArgumentParser(
        description="TRACE AI Computer Vision Subsystem — Vehicle Detection, Tracking, and Kinematics"
    )
    parser.add_argument("--video", required=True, help="Path to input video evidence (.mp4, .mov, .avi)")
    parser.add_argument("--evidence_id", default=None, help="Evidence ID reference (e.g. EVD-VID-01)")
    parser.add_argument("--incident_id", default=None, help="Incident ID reference (e.g. INC-20261030-01)")
    parser.add_argument("--sample_interval", type=int, default=2, help="Process every Nth frame (default: 2)")
    parser.add_argument("--no_render", action="store_true", help="Skip rendering annotated output video")

    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        logger.error("Error: Specified video file does not exist: %s", video_path)
        sys.exit(1)

    result = video_processor.process_video_file(
        video_path=video_path,
        evidence_id=args.evidence_id,
        incident_id=args.incident_id,
        sample_interval=args.sample_interval,
        generate_annotated_video=not args.no_render,
    )

    print("\n" + "=" * 60)
    print("TRACE AI — COMPUTER VISION PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Video Dimensions:    {result.video_metadata.width}x{result.video_metadata.height} @ {result.video_metadata.fps} fps")
    print(f"Duration:            {result.video_metadata.duration_seconds}s ({result.video_metadata.frame_count} frames)")
    print(f"Tracked Vehicles:    {len(result.tracks)}")
    for t in result.tracks:
        print(f"  - [{t.track_id}] {t.class_name.upper()}: {len(t.observations)} observations ({t.apparent_direction}, {t.apparent_state})")
    print(f"Candidate Events:    {len(result.candidate_events)}")
    for e in result.candidate_events:
        print(f"  - [{e.classification}] {e.event_type} at t={e.timestamp_seconds:.2f}s (Track: {e.track_id})")
    if result.annotated_video_path:
        print(f"Annotated Video:     {result.annotated_video_path}")
    print(f"Keyframe Snapshots:  {len(result.extracted_frame_paths)} saved")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
