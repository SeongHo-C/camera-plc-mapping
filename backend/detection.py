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

        # self.depth_estimator = DepthEstimation(device=self.device)

        self.plc_controller = plc_controller

        self.shoot_track_ids = set()
        self.last_shoot_time = 0

        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def detect(self, frame, depth_frame):
        results = self.model.track(
            source=frame,
            tracker='botsort.yaml',
            conf=0.3,  # 검출 신뢰도 임계값. 높이면 오탐↓, 미탐↑
            iou=0.5,  # NMS에서 겹침 허용치. 낮추면 중복↓, 높이면 중복↑
            persist=True,
            verbose=False
        )

        detections = self.parse_results(results[0])

        hornet_detected = any(d['cls_id'] in (0, 1) for d in detections)

        if hornet_detected:
            # depth_map = self.depth_estimator.estimate_depth(frame)
            # self.save_depth_image(depth_map)

            # depth_scale = self.depth_estimator.calibrate_depth_scale(depth_map, (100, 10, 140, 590))

            self.control_shooting(detections, depth_frame)

        return results[0].plot()

    def control_shooting(self, detections, depth_frame):
        if self.plc_controller.shoot_mode == 1:
            self.process_shooting(detections, depth_frame)
        elif self.plc_controller.laser_mode == 1:
            correction = self.plc_controller.laser_correction_value
            self.process_shooting(detections, depth_frame, correction)

    def process_shooting(self, detections, depth_frame, correction_value=0):
        current_time = time.time()

        if current_time - self.last_shoot_time < 3:
            return

        if any(d['cls_id'] == 3 for d in detections):
            print('안전 조치: 사람이 감지되어 사격을 중단합니다.')
            return

        valid_targets = [
            d for d in detections
            if d['cls_id'] in (0, 1)
            and d['track_id'] not in self.shoot_track_ids
        ]

        if valid_targets:
            target = min(valid_targets, key=lambda x: x['track_id'])
            # hornet_distance_cm = self.get_hornet_distance(depth_map, target['bbox'], depth_scale)

            [x_min, y_min, x_max, y_max] = target['bbox']

            x_center = int((x_min + x_max) / 2)
            y_center = int((y_min + y_max) / 2 + correction_value)

            hornet_distance_cm = round(depth_frame.get_distance(x_center, y_center) * 100, 2)

            self.plc_controller.manual_shoot('Pixel', x_center, y_center)
            time.sleep(1)
            self.plc_controller.manual_shoot('Pixel', x_center, y_center, hornet_distance_cm)

            self.shoot_track_ids.add(target['track_id'])
            self.last_shoot_time = current_time

    # def get_hornet_distance(self, depth_map, hornet_bbox, depth_scale):
    #     x_min, y_min, x_max, y_max = map(int, hornet_bbox)
    #     hornet_region = depth_map[y_min:y_max, x_min:x_max]
    #     avg_depth = hornet_region.mean()
    #     hornet_distance_cm = int(depth_scale / avg_depth)
    #     print(hornet_distance_cm)
    #     return hornet_distance_cm

    def parse_results(self, results):
        return [{
            'cls_id': int(box.cls.item()),
            'bbox': box.xyxy[0].tolist(),
            'track_id': int(box.id.item()) if box.id else None
        } for box in results.boxes]

    def save_depth_image(self, depth_map, grayscale=True):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f'depth_{timestamp}.jpg'
        save_path = os.path.join(self.output_dir, filename)

        depth_vis = self.depth_estimator.visualize_depth(
            depth_map,
            grayscale=grayscale
        )

        cv2.imwrite(save_path, depth_vis)
        print(f'[{timestamp}] 깊이 맵 저장 완료: {filename}')
