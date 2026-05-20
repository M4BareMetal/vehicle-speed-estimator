import yaml
from core.video_stream import VideoStream
from core.detector import VehicleDetector
from core.tracker import VehicleTracker
from core.speed_estimator import SpeedEstimator
from core.alert_engine import AlertEngine
from core.reporter import ReportManager
from utils.drawing import draw_tracks_and_speed, draw_stats_overlay


def main():
    config_path = 'config.yaml'

    with open(config_path) as f:
        config = yaml.safe_load(f)

    stream = VideoStream(config_path)
    detector = VehicleDetector(config_path)
    tracker = VehicleTracker(config_path)
    speed_estimator = SpeedEstimator(config_path)
    alert_engine = AlertEngine(config_path)
    reporter = ReportManager(config_path)

    zone_points = config['speed']['measurement_zone']
    speed_limit = config['speed']['speed_limit_kmh']
    total_vehicles = set()
    total_violations = set()

    while True:
        ret, frame, frame_id, timestamp = stream.read()
        if not ret:
            break

        detections = detector.detect(frame)
        tracks = tracker.update(detections, frame)
        speed_data = speed_estimator.update(tracks, frame_id, timestamp)
        alerts = alert_engine.evaluate(speed_data)
        reporter.update(speed_data, alerts, frame, frame_id, timestamp)

        for t in tracks:
            total_vehicles.add(t['track_id'])
        for a in alerts:
            total_violations.add(a['track_id'])

        annotated = draw_tracks_and_speed(frame, tracks, speed_data, alerts, zone_points)
        annotated = draw_stats_overlay(annotated, len(total_vehicles), len(total_violations), speed_limit)

        stream.show(annotated)

        if stream.should_quit():
            break

    reporter.finalize()
    stream.release()
    print(f"\nDone. Total vehicles: {len(total_vehicles)} | Violations: {len(total_violations)}")
    print(f"Log saved to: {config['reporting']['output_csv']}")


if __name__ == '__main__':
    main()
