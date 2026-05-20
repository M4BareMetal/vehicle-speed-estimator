import yaml
from ultralytics import YOLO


CLASS_NAMES = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}


class VehicleDetector:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.model_name = self.config['model']['yolo_model']
        self.allowed_classes = self.config['model']['classes']
        self.conf_threshold = self.config['model']['confidence_threshold']
        self.model = self._load_model()

    def _load_model(self):
        return YOLO(self.model_name)

    def detect(self, frame):
        results = self.model(frame, conf=self.conf_threshold, verbose=False)[0]
        detections = []
        for box in results.boxes:
            class_id = int(box.cls[0])
            if class_id not in self.allowed_classes:
                continue
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            conf = float(box.conf[0])
            detections.append({
                'bbox': [x1, y1, x2, y2],
                'confidence': conf,
                'class_id': class_id,
                'class_name': CLASS_NAMES.get(class_id, 'vehicle')
            })
        return detections
