import torch
from ultralytics import YOLO


class Detection:
    def __init__(self, model_path='weights/detect11m.pt'):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f'device: {self.device}')

        self.model = YOLO(model_path)
        self.model.to(self.device)

    def detect(self, frame):
        results = self.model.track(
            source=frame,
            tracker='botsort.yaml',
            conf=0.3,  # 검출 신뢰도 임계값. 높이면 오탐↓, 미탐↑
            iou=0.6,  # NMS에서 겹침 허용치. 낮추면 중복↓, 높이면 중복↑
            persist=True,
            verbose=False
        )
        return results[0].plot()
