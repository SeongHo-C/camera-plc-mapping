import torch
import time
import os
import cv2
from ultralytics import YOLO
from depth.estimation import DepthEstimation
from datetime import datetime


class Detection:
    def __init__(self, plc_controller, model_path='weights/detect11s.pt', output_dir='./saved_depth'):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f'device: {self.device}')

        self.model = YOLO(model_path).to(self.device)
        self.class_names = self.model.names

        self.depth_estimator = DepthEstimation(device=self.device)

        self.plc_controller = plc_controller

        self.shoot_track_ids = set()
        self.last_shoot_time = 0

        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def detect(self, frame):
        results = self.model.track(
            source=frame,
            tracker='botsort.yaml',
            conf=0.0,  # 검출 신뢰도 임계값. 높이면 오탐↓, 미탐↑
            iou=0.5,  # NMS에서 겹침 허용치. 낮추면 중복↓, 높이면 중복↑
            persist=True,
            verbose=False
        )

        detections = self.parse_results(results[0])

        hornet_detected = any(d['cls_id'] in (0, 1) for d in detections)

        depth_map = None
        if hornet_detected:
            depth_map = self.depth_estimator.estimate_depth(frame)
            # self.save_depth_image(depth_map)

        self.conrol_shooting(detections, depth_map)

        # if self.plc_controller.shoot_mode == 1:
        #     self.control_shoot(detections)
        # elif self.plc_controller.laser_mode == 1:
        #     self.control_shoot(detections, self.plc_controller.laser_correction_value)

        return results[0].plot()

    def control_shooting(self, detections, depth_map):
        if self.plc_controller.shoot_mode == 1:
            self.process_shooting(detections, depth_map)
        elif self.plc_controller.laser_mode == 1:
            correction = self.plc_controller.laser_correction_value
            self.process_shooting(detections, depth_map, correction)

    # def process_shooting(self, detections, depth_map, correction_value=0):
        # current_time = time.time()

        # if current_time - self.last_shoot_time < 2:
        #     return

        # classes = {d['cls_id'] for d in detections}
        # hornets = [
        #     d for d in detections
        #     if d['cls_id'] in (0, 1)
        #     and d['track_id'] is not None
        #     and d['track_id'] not in self.shoot_track_ids
        # ]

        # if 3 in classes:
        #     print('사람이 탐지되었으므로, 사격 중지')
        #     return

        # if hornets:
        #     target = min(hornets, key=lambda x: x['track_id'])
        #     [x_min, y_min, x_max, y_max] = target['bbox']

        #     x_center = int((x_min + x_max) / 2)
        #     y_center = int((y_min + y_max) / 2 + correction_value)

        #     self.plc_controller.manual_shoot('Pixel', x_center, y_center)
        #     self.plc_controller.manual_shoot('Pixel', x_center + 1, y_center)

        #     self.shoot_track_ids.add(target['track_id'])
        #     self.last_shoot_time = current_time

    def parse_results(self, results):
        return [{
            'cls_id': int(box.cls.item()),
            'bbox': box.xyxy[0].tolist(),
            'track_id': int(box.id.item()) if box.id else None
        } for box in results.boxes]

    def save_depth_image(self, depth_map, grayscale=True):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f'depth_{timestamp}.png'
        save_path = os.path.join(self.output_dir, filename)

        depth_vis = self.depth_estimator.visualize_depth(
            depth_map,
            grayscale=grayscale
        )

        cv2.imwrite(save_path, depth_vis)
        print(f'[{timestamp}] 깊이 맵 저장 완료: {filename}')
