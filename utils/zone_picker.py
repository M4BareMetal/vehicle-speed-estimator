
import cv2
import yaml
import sys
import os

points = []


def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
        points.append([x, y])
        print(f"Point {len(points)}: ({x}, {y})")
        cv2.circle(param, (x, y), 6, (0, 255, 255), -1)
        if len(points) > 1:
            cv2.line(param, tuple(points[-2]), tuple(points[-1]), (0, 255, 255), 2)
        if len(points) == 4:
            cv2.line(param, tuple(points[-1]), tuple(points[0]), (0, 255, 255), 2)
        cv2.imshow('Zone Picker', param)


def main():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(config_path) as f:
        config = yaml.safe_load(f)

    source = config['source']
    if source['type'] == 'video':
        cap = cv2.VideoCapture(source['path'])
    else:
        cap = cv2.VideoCapture(source.get('webcam_index', 0))

    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("ERROR: Could not read frame from video source.")
        sys.exit(1)

    clone = frame.copy()
    cv2.imshow('Zone Picker', clone)
    cv2.setMouseCallback('Zone Picker', click_event, clone)

    print("Click 4 points to define the measurement zone. Press ENTER when done.")
    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == 13 and len(points) == 4:  # Enter key
            break
        elif key == 27:  # Esc
            print("Cancelled.")
            cv2.destroyAllWindows()
            sys.exit(0)

    cv2.destroyAllWindows()
    config['speed']['measurement_zone'] = points
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f"\nZone saved to config.yaml:")
    for i, p in enumerate(points):
        print(f"  Point {i+1}: {p}")


if __name__ == '__main__':
    main()

    