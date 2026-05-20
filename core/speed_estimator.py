import yaml
import numpy as np
from utils.calibration import get_perspective_transform, transform_point


class SpeedEstimator:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.track_history = {}
        self.speed_cache = {}

        zone_cfg = self.config['speed']
        self.zone_points = zone_cfg['measurement_zone']
        self.real_world_zone = zone_cfg['real_world_zone_meters']

        # Build perspective transform matrix
        self.transform_matrix = get_perspective_transform(
            self.zone_points,
            self.real_world_zone
        )

    def _in_zone(self, point):
        import cv2

        # Handle None or weird inputs
        if point is None:
            return False

        # Convert to numpy array and flatten
        p = np.array(point, dtype=float).reshape(-1)

        # Need at least x and y
        if p.size < 2:
            return False

        x, y = float(p[0]), float(p[1])

        pts = np.array(self.zone_points, dtype=np.float32)
        return cv2.pointPolygonTest(pts, (x, y), False) >= 0

    def update(self, tracks, frame_id, timestamp):
        speed_results = []

        for track in tracks:
            track_id = track['track_id']
            centroid = track['centroid']

            # Initialize history list for this track
            if track_id not in self.track_history:
                self.track_history[track_id] = []

            # Only record positions when inside the measurement zone
            if self._in_zone(centroid):
                self.track_history[track_id].append({
                    'frame_id': frame_id,
                    'timestamp': timestamp,
                    'centroid': centroid
                })

            # Default: use cached speed if already computed
            speed_kmh = self.speed_cache.get(track_id)

            history = self.track_history.get(track_id, [])
            if len(history) >= 2:
                p1 = history[-2]
                p2 = history[-1]
                dt = p2['timestamp'] - p1['timestamp']

                if dt > 0:
                        try:
                            w1 = transform_point(p1['centroid'], self.transform_matrix)
                            w2 = transform_point(p2['centroid'], self.transform_matrix)
                            dist_m = float(np.linalg.norm(np.array(w2) - np.array(w1)))
                            speed_ms = dist_m / dt
                            speed_kmh = round(speed_ms * 3.6, 2)
                            self.speed_cache[track_id] = speed_kmh
                        except Exception as e:
                            # If transform fails for any reason, keep previous speed or None
                            speed_kmh = self.speed_cache.get(track_id)

            speed_results.append({
                'track_id': track_id,
                'class_name': track.get('class_name', 'vehicle'),
                'speed_kmh': speed_kmh,
                'bbox': track['bbox'],
                'centroid': centroid,
                'timestamp': timestamp
            })

        return speed_results