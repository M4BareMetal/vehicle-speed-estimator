import yaml


class AlertEngine:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.speed_limit = self.config['speed']['speed_limit_kmh']

    def evaluate(self, speed_data):
        alerts = []
        for item in speed_data:
            speed = item.get('speed_kmh')
            if speed is not None and speed > self.speed_limit:
                alerts.append({
                    'track_id': item['track_id'],
                    'status': 'overspeed',
                    'speed_kmh': speed,
                    'timestamp': item['timestamp']
                })
        return alerts
