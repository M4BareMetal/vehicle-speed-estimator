import cv2
import yaml


class VideoStream:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        source_cfg = self.config['source']
        self.window_name = self.config['ui']['window_name']

        if source_cfg['type'] == 'video':
            self.cap = cv2.VideoCapture(source_cfg['path'])
        else:
            self.cap = cv2.VideoCapture(source_cfg.get('webcam_index', 0))

        self.frame_id = 0
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30

    def read(self):
        ret, frame = self.cap.read()
        if not ret:
            return False, None, None, None

        timestamp = self.frame_id / self.fps
        current_id = self.frame_id
        self.frame_id += 1
        return True, frame, current_id, timestamp

    def show(self, frame):
        if self.config['ui'].get('show_live', True):
            cv2.imshow(self.window_name, frame)

    def should_quit(self):
        return cv2.waitKey(1) & 0xFF == ord('q')

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
