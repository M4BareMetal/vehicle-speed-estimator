import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.alert_engine import AlertEngine


def test_overspeed_detection():
    engine = AlertEngine('config.yaml')
    speed_data = [
        {'track_id': 1, 'speed_kmh': 80, 'timestamp': 1.0},
        {'track_id': 2, 'speed_kmh': 45, 'timestamp': 1.0},
        {'track_id': 3, 'speed_kmh': None, 'timestamp': 1.0},
    ]
    alerts = engine.evaluate(speed_data)
    assert len(alerts) == 1
    assert alerts[0]['track_id'] == 1
    assert alerts[0]['status'] == 'overspeed'
    print("Alert engine test passed.")


if __name__ == '__main__':
    test_overspeed_detection()
