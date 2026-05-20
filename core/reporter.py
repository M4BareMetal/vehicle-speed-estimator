import csv
import os
import yaml
import cv2


class ReportManager:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.output_csv = self.config['reporting']['output_csv']
        self.violation_dir = self.config['reporting']['violation_frames_dir']
        os.makedirs(os.path.dirname(self.output_csv), exist_ok=True)
        os.makedirs(self.violation_dir, exist_ok=True)
        self.rows = []
        self.logged_violations = set()

    def update(self, speed_data, alerts, frame, frame_id, timestamp):
        for item in speed_data:
            self.rows.append([frame_id, timestamp, item['track_id'], item['class_name'], item['speed_kmh']])
        for alert in alerts:
            key = (alert['track_id'], frame_id)
            if key not in self.logged_violations:
                self.logged_violations.add(key)
                filename = os.path.join(self.violation_dir, f"vehicle_{alert['track_id']}_frame_{frame_id}.jpg")
                cv2.imwrite(filename, frame)

    def finalize(self):
        with open(self.output_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['frame_id', 'timestamp', 'track_id', 'class_name', 'speed_kmh'])
            writer.writerows(self.rows)
