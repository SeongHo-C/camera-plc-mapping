import torch
from ultralytics import YOLO


class Detection:
    def __init__(self, model_path='weights/detect11m.pt'):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f'device: {self.device}')

        self.model = YOLO(model_path)
        self.model.to(self.device)

    def detect(self, frame):
        results = self.model(frame, verbose=False)
        return results[0].plot()
