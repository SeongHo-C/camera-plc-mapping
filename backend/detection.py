import torch
from ultralytics import YOLO


class Detection:
    def __init__(self, model_path='weights/detect11m.pt'):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f'device: {self.device}')

        self.model = YOLO(model_path)
        self.model.to(self.device)

        self.class_names = self.model.names
        print(self.class_names)

    def detect(self, frame):
        results = self.model.track(
            source=frame,
            tracker='botsort.yaml',
            conf=0.3,  # 검출 신뢰도 임계값. 높이면 오탐↓, 미탐↑
            iou=0.5,  # NMS에서 겹침 허용치. 낮추면 중복↓, 높이면 중복↑
            persist=True,
            verbose=False
        )

        detections = self.parse_results(results)
        print(detections)

        return results[0].plot()

    def parse_results(self, results):
        detections = []

        for box in results[0].boxes:
            cls_id = int(box.cls.item())
            bbox = box.xyxy[0].tolist()
            track_id = int(box.id.item()) if box.id is not None else None

            detections.append({
                'class': self.class_names[cls_id],
                'bbox': bbox,
                'track_id': track_id
            })

        return detections
