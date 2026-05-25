import cv2
import numpy as np
import base64
import json
import os
import sys
import yaml
import time

# Make sure core is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.detector import VehicleDetector
from core.tracker import VehicleTracker
from core.speed_estimator import SpeedEstimator
from core.alert_engine import AlertEngine
from core.reporter import ReportManager
from utils.drawing import draw_tracks_and_speed, draw_stats_overlay


def frame_to_base64(frame: np.ndarray, quality: int = 75) -> str:
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return base64.b64encode(buf).decode('utf-8')


def get_first_frame_b64(video_path: str) -> str:
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise ValueError("Could not read video file")
    return frame_to_base64(frame, quality=90)


def run_pipeline(video_path: str, zone_points: list, speed_limit: int, config_path: str):
    """
    Generator that yields SSE-formatted JSON strings.
    Each event is one of:
      - {"type": "frame", "data": "<base64 jpeg>", "stats": {...}}
      - {"type": "done",  "summary": {...}}
      - {"type": "error", "message": "..."}
    """
    try:
        # Patch config with user-supplied zone and video path
        with open(config_path) as f:
            config = yaml.safe_load(f)

        config['source']['type'] = 'video'
        config['source']['path'] = video_path
        config['speed']['measurement_zone'] = zone_points
        config['speed']['speed_limit_kmh'] = speed_limit
        config['ui']['show_live'] = False  # headless

        # Write patched config to a temp file
        temp_config = config_path.replace('config.yaml', '_runtime_config.yaml')
        with open(temp_config, 'w') as f:
            yaml.dump(config, f)

        # Init pipeline components
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        detector = VehicleDetector(temp_config)
        tracker = VehicleTracker(temp_config)
        speed_estimator = SpeedEstimator(temp_config)
        alert_engine = AlertEngine(temp_config)
        reporter = ReportManager(temp_config)

        total_vehicles = set()
        total_violations = set()
        frame_id = 0
        STREAM_EVERY = 2  # Send every Nth frame to keep bandwidth sane

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = frame_id / fps

            detections = detector.detect(frame)
            tracks = tracker.update(detections, frame)
            speed_data = speed_estimator.update(tracks, frame_id, timestamp)
            alerts = alert_engine.evaluate(speed_data)
            reporter.update(speed_data, alerts, frame, frame_id, timestamp)

            for t in tracks:
                total_vehicles.add(t['track_id'])
            for a in alerts:
                total_violations.add(a['track_id'])

            if frame_id % STREAM_EVERY == 0:
                annotated = draw_tracks_and_speed(
                    frame.copy(), tracks, speed_data, alerts, zone_points
                )
                annotated = draw_stats_overlay(
                    annotated, len(total_vehicles), len(total_violations), speed_limit
                )

                b64 = frame_to_base64(annotated, quality=70)
                progress = round((frame_id / max(total_frames, 1)) * 100, 1)

                payload = json.dumps({
                    "type": "frame",
                    "data": b64,
                    "stats": {
                        "vehicles": len(total_vehicles),
                        "violations": len(total_violations),
                        "frame": frame_id,
                        "total_frames": total_frames,
                        "progress": progress,
                        "fps": round(fps, 1)
                    }
                })
                yield f"data: {payload}\n\n"

            frame_id += 1

        cap.release()
        reporter.finalize()

        # Build violation list for frontend
        violation_dir = config['reporting']['violation_frames_dir']
        violation_files = []
        if os.path.exists(violation_dir):
            for fname in sorted(os.listdir(violation_dir)):
                if fname.endswith('.jpg'):
                    fpath = os.path.join(violation_dir, fname)
                    with open(fpath, 'rb') as vf:
                        vb64 = base64.b64encode(vf.read()).decode('utf-8')
                    violation_files.append({
                        "filename": fname,
                        "image": vb64
                    })

        # Read CSV summary
        csv_path = config['reporting']['output_csv']
        speed_records = []
        if os.path.exists(csv_path):
            import csv
            with open(csv_path) as cf:
                reader = csv.DictReader(cf)
                for row in reader:
                    speed_records.append(row)

        summary_payload = json.dumps({
            "type": "done",
            "summary": {
                "total_vehicles": len(total_vehicles),
                "total_violations": len(total_violations),
                "speed_limit": speed_limit,
                "total_frames": total_frames,
                "violations": violation_files[:20],  # cap at 20 for payload size
                "records": speed_records
            }
        })
        yield f"data: {summary_payload}\n\n"

    except Exception as e:
        import traceback
        err = json.dumps({"type": "error", "message": str(e), "trace": traceback.format_exc()})
        yield f"data: {err}\n\n"
