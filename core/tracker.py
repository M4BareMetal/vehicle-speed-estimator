import yaml
import numpy as np
from collections import defaultdict

# SORT implementation (minimal, no external dep)
# For production use: pip install sort-tracker
# Here we ship a lightweight SORT-like tracker inline

class KalmanBoxTracker:
    count = 0
    def __init__(self, bbox):
        from filterpy.kalman import KalmanFilter
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.eye(7)
        for i in range(4): self.kf.F[i, i+3] = 1
        self.kf.H = np.eye(4, 7)
        self.kf.R[2:, 2:] *= 10
        self.kf.P[4:, 4:] *= 1000
        self.kf.P *= 10
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01
        self.kf.x[:4] = self._bbox_to_z(bbox)
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0

    def _bbox_to_z(self, bbox):
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = bbox[0] + w / 2
        y = bbox[1] + h / 2
        s = w * h
        r = w / float(h)
        return np.array([x, y, s, r]).reshape((4, 1))

    def _x_to_bbox(self, x):
        w = np.sqrt(abs(x[2] * x[3]))
        h = x[2] / w
        return [x[0] - w/2, x[1] - h/2, x[0] + w/2, x[1] + h/2]

    def update(self, bbox):
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(self._bbox_to_z(bbox))

    def predict(self):
        if self.kf.x[6] + self.kf.x[2] <= 0:
            self.kf.x[6] = 0
        self.kf.predict()
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(self._x_to_bbox(self.kf.x))
        return self.history[-1]

    def get_state(self):
        return self._x_to_bbox(self.kf.x)


def iou(bb_test, bb_gt):
    # Convert to flat numpy arrays
    bb_test = np.array(bb_test, dtype=float).reshape(-1)
    bb_gt = np.array(bb_gt, dtype=float).reshape(-1)

    if bb_test.size < 4 or bb_gt.size < 4:
        return 0.0

    x1, y1, x2, y2 = bb_test[:4]
    gx1, gy1, gx2, gy2 = bb_gt[:4]

    xx1 = max(x1, gx1)
    yy1 = max(y1, gy1)
    xx2 = min(x2, gx2)
    yy2 = min(y2, gy2)

    w = max(0.0, xx2 - xx1)
    h = max(0.0, yy2 - yy1)
    inter = w * h

    area1 = max(0.0, (x2 - x1) * (y2 - y1))
    area2 = max(0.0, (gx2 - gx1) * (gy2 - gy1))

    denom = area1 + area2 - inter + 1e-6
    return float(inter / denom) if denom > 0 else 0.0

def associate_detections(detections, trackers, iou_threshold=0.3):
    if len(trackers) == 0:
        return np.empty((0, 2), dtype=int), list(range(len(detections))), []

    iou_matrix = np.zeros((len(detections), len(trackers)))
    for d, det in enumerate(detections):
        for t, trk in enumerate(trackers):
            iou_matrix[d, t] = iou(det, trk)

    from scipy.optimize import linear_sum_assignment
    row_ind, col_ind = linear_sum_assignment(-iou_matrix)

    matched, unmatched_d, unmatched_t = [], [], []
    for d in range(len(detections)):
        if d not in row_ind:
            unmatched_d.append(d)
    for t in range(len(trackers)):
        if t not in col_ind:
            unmatched_t.append(t)
    for r, c in zip(row_ind, col_ind):
        if iou_matrix[r, c] < iou_threshold:
            unmatched_d.append(r)
            unmatched_t.append(c)
        else:
            matched.append([r, c])

    return np.array(matched), unmatched_d, unmatched_t


class VehicleTracker:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        cfg = self.config['tracking']
        self.max_age = cfg['max_age']
        self.min_hits = cfg['min_hits']
        self.iou_threshold = cfg['iou_threshold']
        self.trackers = []
        self.frame_count = 0
        self.class_map = {}

    def update(self, detections, frame):
        self.frame_count += 1
        trk_boxes = []
        for t in self.trackers:
            pred = t.predict()
            trk_boxes.append(pred)

        det_boxes = [d['bbox'] for d in detections]
        matched, unmatched_d, unmatched_t = associate_detections(det_boxes, trk_boxes, self.iou_threshold)

        for m in matched:
            self.trackers[m[1]].update(det_boxes[m[0]])
            self.class_map[self.trackers[m[1]].id] = detections[m[0]]['class_name']

        for i in unmatched_d:
            t = KalmanBoxTracker(det_boxes[i])
            self.class_map[t.id] = detections[i]['class_name']
            self.trackers.append(t)

        results = []
        self.trackers = [t for t in self.trackers if t.time_since_update <= self.max_age]

        for t in self.trackers:
            if t.time_since_update == 0 and (t.hit_streak >= self.min_hits or self.frame_count <= self.min_hits):
                state = t.get_state()
                x1, y1, x2, y2 = state
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                results.append({
                    'track_id': t.id,
                    'bbox': [x1, y1, x2, y2],
                    'centroid': (cx, cy),
                    'class_name': self.class_map.get(t.id, 'vehicle')
                })
        return results
