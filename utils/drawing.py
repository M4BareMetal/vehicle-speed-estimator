import cv2
import numpy as np


def draw_measurement_zone(frame, zone_points, color=(255, 255, 0)):
    pts = np.array(zone_points, dtype=np.int32).reshape((-1, 1, 2))
    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)
    x = int(zone_points[0][0])
    y = int(zone_points[0][1]) - 10
    cv2.putText(frame, 'Speed Measurement Zone', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)


def draw_tracks_and_speed(frame, tracks, speed_data, alerts, zone_points=None):
    if zone_points:
        draw_measurement_zone(frame, zone_points)
    alert_ids = {a['track_id'] for a in alerts}
    speed_map = {item['track_id']: item for item in speed_data}
    for track in tracks:
        bbox = np.array(track['bbox'], dtype=float).reshape(-1)
        if bbox.size < 4:
            continue
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        track_id = track['track_id']
        item = speed_map.get(track_id, {})
        speed = item.get('speed_kmh')
        class_name = track.get('class_name', 'vehicle')
        color = (0, 0, 255) if track_id in alert_ids else (0, 255, 0)
        status = 'OVERSPEED' if track_id in alert_ids else 'OK'
        label = f"ID:{track_id} {class_name}"
        speed_label = f"{speed:.1f} km/h [{status}]" if speed is not None else "Estimating..."
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, int(max(20, y1 - 20))), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        cv2.putText(frame, speed_label, (x1, int(max(38, y1 - 5))), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return frame


def draw_stats_overlay(frame, total_vehicles, violations, speed_limit):
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (300, 100), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
    cv2.putText(frame, f'Speed Limit: {speed_limit} km/h', (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f'Vehicles: {total_vehicles}', (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f'Violations: {violations}', (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    return frame