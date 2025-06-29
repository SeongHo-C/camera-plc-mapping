import time
import cv2
import numpy as np
from pyModbusTCP.client import ModbusClient


class PlcController:
    def __init__(self):
        # self.client = ModbusClient(host='192.168.1.10', port=502)
        self.shoot_mode = 0
        self.laser_mode = 0
        self.laser_correction_value = 0

        # if self.client.open():
        #     if self.client.write_single_register(1800, 0):  # 발사
        #         print('발사 허용 안함 쓰기 성공')
        #     else:
        #         print('발사 허용 안함 쓰기 실패')

        #     self.client.write_single_register(1805, 0)  # 레이저

        self.BASE_DEPTH = 85.0
        self.homography_mat = None

    # def manual_shoot(self, mode, x, y, z=None):
    def manual_shoot(self, mode, x, y):
        if mode == 'PLC':
            """
            if self.client.write_single_register(1500, int(x)):
                self.client.write_single_register(1600, int(y))
                print(f'PLC 좌표 쓰기 성공: {x}, {y}')
            else:
                print('PLC 좌표 쓰기 실패')
            """
            print(f'PLC 좌표 쓰기 성공: {x}, {y}')
            return x, y
        elif mode == 'Pixel':
            # plc_x, plc_y = self.pixel_to_plc(x, y, z)
            plc_x, plc_y = self.pixel_to_plc(x, y)

            """
            if self.client.write_single_register(1500, plc_x):
                self.client.write_single_register(1600, plc_y)
                print(f'PLC 좌표 쓰기 성공: {plc_x}, {plc_y}')
            else:
                print('PLC 좌표 쓰기 실패')
            """
            # print(f'PLC 좌표 쓰기 성공: {plc_x}, {plc_y}')
            return plc_x, plc_y
        elif mode == 'test':
            # 연속된 주소(1500, 1501)로 변경 희망, 하나의 주소만을 쓰더라도 사격이 되는지 확인 필요
            """
            if self.client.write_multiple_registers(1500, [int(x), int(y)]):
                print(f'PLC 좌표 쓰기 성공: {x}, {y}')
            else:
                print('PLC 좌표 쓰기 실패')
            """
            print(f'PLC 좌표 쓰기 성공: {x}, {y}')
            return x, y

    def continuous_shoot(self, corner):
        targets = list()

        for coordinate in corner:
            x = int(coordinate['x'])
            y = int(coordinate['y'])

            """
            if self.client.write_single_register(1500, x):
                self.client.write_single_register(1600, y)
                print(f'PLC 좌표 쓰기 성공: {x}, {y}')
            else:
                print(f'PLC 좌표 쓰기 실패: {x}, {y}')
            """
            print(f'PLC 좌표 쓰기 성공: {x}, {y}')
            targets.append((x, y))
            time.sleep(2)

        return tuple(targets)

    # def pixel_to_plc(self, x, y, z=None):
    def pixel_to_plc(self, x, y):
        if self.homography_mat is None:
            raise ValueError('호모그래피 행렬이 계산되지 않았습니다.')

        # if z:
        #     scale = self.BASE_DEPTH / z
        #     pixel_vec = np.array([x * scale, y * scale, 1], dtype=np.float32)
        #     plc_vec = self.homography_mat @ pixel_vec
        #     return round(plc_vec[0] / plc_vec[2]), round(plc_vec[1] / plc_vec[2])
        # else:

        pixel_vec = np.array([x, y], dtype=np.float32).reshape(1, 1, 2)
        plc_vec = cv2.perspectiveTransform(pixel_vec, self.homography_mat)
        return round(plc_vec[0][0][0]), round(plc_vec[0][0][1])

    def calculate_homography_matrix(self, mapping_items):
        self.src_pts = np.array(mapping_items['Pixel'], dtype=np.float32)
        self.dst_pts = np.array(mapping_items['PLC'], dtype=np.float32)

        # 호모그래피 계산
        # 임계값 1.0~5.0 사이에서 최적 값 실험
        H, status = cv2.findHomography(
            self.src_pts, self.dst_pts,
            method=cv2.LMEDS,
            # ransacReprojThreshold=3.0,
            # maxIters=2000,
            confidence=0.999
        )

        # inliers_src = self.src_pts[status.ravel() == 1]
        # inliers_dst = self.dst_pts[status.ravel() == 1]

        # if len(inliers_src) >= 8:
        #     # 인라이어만으로 정밀 호모그래피 계산
        #     H_refined, _ = cv2.findHomography(
        #         inliers_src, inliers_dst,
        #         method=cv2.LMEDS,
        #         confidence=0.999
        #     )
        #     self.homography_mat = H_refined if H_refined is not None else H
        # else:
        self.homography_mat = H

        # 인라이어 비율 확인 (품질 체크)
        inlier_ratio = np.sum(status) / len(status)
        print(f'인라이어 비율: {inlier_ratio:.2f}')

    def plc_control(self, address, mode):
        # if self.client.write_single_register(address, mode):
        #     print(f'{address} 주소 쓰기 성공: {mode}')
        # else:
        #     print(f'{address} 주소 쓰기 실패')

        if address == 1800:
            self.shoot_mode = mode
        elif address == 1805:
            self.laser_mode = mode

        print(f'{address} 주소 쓰기 성공: {mode}')

    def validate_mapping(self):
        errors = []

        for pixel, plc in zip(self.src_pts, self.dst_pts):
            converted = self.pixel_to_plc(pixel[0], pixel[1])

            error = np.linalg.norm(np.array(plc) - np.array(converted))
            errors.append(error)

            print(f'픽셀 {pixel} → PLC {converted} | 오차: {error:.2f}')

        return round(max(errors), 2), round(np.mean(errors), 2)
