import torch
import time
import os
import cv2
import json
import numpy as np
from ultralytics import YOLO
# from depth.estimation import DepthEstimation
from datetime import datetime
from collections import defaultdict


class Detection:
    def __init__(self, plc_controller, model_path='weights/detect11m.pt', output_dir='./saved_depth'):
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

        self.current_track_history = []
        self.current_lowest_id = None
        self.max_history_length = 30
        self.last_detect_time = None
        self.track_timeout = 1.0

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
            print(f'인식 시간 >>> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            # depth_map = self.depth_estimator.estimate_depth(frame)
            # self.save_depth_image(depth_map)

            # depth_scale = self.depth_estimator.calibrate_depth_scale(depth_map, (100, 10, 140, 590))
            # self.control_shooting(detections, depth_frame)
            self.control_shooting(detections)

        plotted_image = results[0].plot()

        if not plotted_image.flags.writeable:
            plotted_image = np.copy(plotted_image)
            plotted_image = plotted_image.astype(np.uint8)

        if len(self.current_track_history) > 1:
            points = np.array(self.current_track_history, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(plotted_image, [points], isClosed=False, color=(255, 255, 255), thickness=2)

        return plotted_image

    # def control_shooting(self, detections, depth_frame):
    def control_shooting(self, detections):
        if self.plc_controller.shoot_mode == 1:
            # self.process_shooting(detections, depth_frame)
            self.process_shooting(detections)
        elif self.plc_controller.laser_mode == 1:
            correction = self.plc_controller.laser_correction_value
            # self.process_shooting(detections, depth_frame, correction)
            self.process_shooting(detections, correction)

    # def process_shooting(self, detections, depth_frame, correction_value=0):
    def process_shooting(self, detections, correction_value=0):
        current_time = time.time()

        if any(d['cls_id'] == 3 for d in detections):
            print('안전 조치: 사람이 감지되어 사격을 중단합니다.')
            return

        valid_targets = [
            d for d in detections
            if d['cls_id'] in (0, 1)
            # and d['track_id'] not in self.shoot_track_ids
        ]

        if valid_targets:
            target = min(valid_targets, key=lambda x: x['track_id'])
            # hornet_distance_cm = self.get_hornet_distance(depth_map, target['bbox'], depth_scale)

            if self.current_lowest_id != target['track_id']:
                self.current_track_history = []

            self.current_lowest_id = target['track_id']
            self.last_detect_time = current_time

            [x_min, y_min, x_max, y_max] = target['bbox']
            x_center = round((x_min + x_max) / 2)
            y_center = round((y_min + y_max) / 2 + correction_value)

            # hornet_distance_cm = round(depth_frame.get_distance(x_center, y_center) * 100, 2)

            self.current_track_history.append((x_center, y_center))

            if len(self.current_track_history) > self.max_history_length:
                self.current_track_history.pop(0)

            if current_time - self.last_shoot_time < 1:
                return

            plc_x, plc_y = self.plc_controller.manual_shoot('Pixel', x_center, y_center)
            self.last_shoot_time = current_time

            print(f'발사 시간 >>> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            # time.sleep(1)
            # self.plc_controller.manual_shoot('Pixel', x_center, y_center, hornet_distance_cm)

            # self.shoot_track_ids.add(target['track_id'])

            # print(f'타겟 {target["track_id"]}: {plc_x}, {plc_y}')
        else:
            if self.last_detect_time and (current_time - self.last_detect_time < self.track_timeout):
                pass
            else:
                self.current_track_history = []
                self.current_lowest_id = None

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

    # def save_depth_image(self, depth_map, grayscale=True):
    #     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    #     filename = f'depth_{timestamp}.jpg'
    #     save_path = os.path.join(self.output_dir, filename)

    #     depth_vis = self.depth_estimator.visualize_depth(
    #         depth_map,
    #         grayscale=grayscale
    #     )

    #     cv2.imwrite(save_path, depth_vis)
    #     print(f'[{timestamp}] 깊이 맵 저장 완료: {filename}')

    async def file_detect(self, websocket, file):
        nparr = np.frombuffer(file, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        results = self.model(
            source=img,
            conf=0.3,  # 검출 신뢰도 임계값. 높이면 오탐↓, 미탐↑
            iou=0.5,  # NMS에서 겹침 허용치. 낮추면 중복↓, 높이면 중복↑
            verbose=False
        )

        save_dir = 'data/captures/result_image'
        os.makedirs(save_dir, exist_ok=True)

        filename = datetime.now().strftime('%Y%m%d_%H%M%S') + '.jpg'
        cv2.imwrite(os.path.join(save_dir, filename), results[0].plot())

        _, buffer = cv2.imencode('.jpg', results[0].plot())
        await websocket.send(json.dumps({'type': 'result', 'mimetype': 'image/jpeg'}))
        await websocket.send(buffer.tobytes())

        return True
