import torch
import time
from ultralytics import YOLO


class Detection:
    def __init__(self, plc_controller, model_path='weights/detect11m.pt'):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f'device: {self.device}')

        self.model = YOLO(model_path)
        self.model.to(self.device)

        self.class_names = self.model.names
        print(self.class_names)

        self.plc_controller = plc_controller
        self.shoot_track_ids = set()
        self.last_shoot_time = 0

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
        if self.plc_controller.shootMode == 1:
            self.control_shoot(detections)

        return results[0].plot()

    def parse_results(self, results):
        detections = []

        for box in results[0].boxes:
            cls_id = int(box.cls.item())
            bbox = box.xyxy[0].tolist()
            track_id = int(box.id.item()) if box.id is not None else None

            detections.append({
                'cls_id': cls_id,
                'bbox': bbox,
                'track_id': track_id
            })

        return detections

    def control_shoot(self, detections):
        current_time = time.time()

        if current_time - self.last_shoot_time < 2:
            return

        classes = {d['cls_id'] for d in detections}
        hornets = [
            d for d in detections
            if d['cls_id'] in (0, 1)
            and d['track_id'] is not None
            and d['track_id'] not in self.shoot_track_ids
        ]

        if 3 in classes:
            print('사람이 탐지되었으므로, 사격 중지')
            return

        if hornets:
            target = min(hornets, key=lambda x: x['track_id'])
            [x_min, y_min, x_max, y_max] = target['bbox']

            x_center = int((x_min + x_max) / 2)
            y_center = int((y_min + y_max) / 2)

            self.plc_controller.manual_shoot('Pixel', x_center, y_center)
            self.plc_controller.manual_shoot('Pixel', x_center + 1, y_center)

            self.shoot_track_ids.add(target['track_id'])
            self.last_shoot_time = current_time
