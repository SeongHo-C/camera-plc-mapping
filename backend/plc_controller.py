import time
import cv2
import numpy as np
from pyModbusTCP.client import ModbusClient


class PlcController:
    def __init__(self):
        self.client = ModbusClient(host='192.168.1.10', port=502)

        if self.client.open():
            if self.client.write_single_register(1800, 0):  # 발사
                print('발사 허용 안함 쓰기 성공')
                time.sleep(0.05)
            else:
                print('발사 허용 안함 쓰기 실패')

            self.client.write_single_register(1805, 0)  # 레이저

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
            plc_x, plc_y = self.pixel_to_plc(x, y)

            """
            if self.client.write_single_register(1500, plc_x):
                self.client.write_single_register(1600, plc_y)
                print(f'PLC 좌표 쓰기 성공: {plc_x}, {plc_y}')
            else:
                print('PLC 좌표 쓰기 실패')
            """
            print(f'PLC 좌표 쓰기 성공: {plc_x}, {plc_y}')
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
            time.sleep(2)

    def pixel_to_plc(self, x, y):
        pixel_vec = np.array([x, y], dtype=np.float32).reshape(1, 1, 2)
        plc_vec = cv2.perspectiveTransform(pixel_vec, self.homography_mat)

        return round(plc_vec[0][0][0]), round(plc_vec[0][0][1])

    def calculate_homography_matrix(self, mapping_items):
        mapping_items = {
            'Pixel': [[111, 38], [582, 48], [73, 434], [619, 460], [192, 105], [499, 114], [177, 344], [510, 354], [268, 161], [419, 167], [262, 277], [423, 283]],
            'PLC': [[7400, 4000], [2600, 4000], [7400, 400], [2600, 400], [6600, 3400], [3400, 3400], [6600, 1000], [3400, 1000], [5800, 2800], [4200, 2800], [5800, 1600], [4200, 1600]]
        }

        src_pts = np.array(mapping_items['Pixel'], dtype=np.float32)
        dst_pts = np.array(mapping_items['PLC'], dtype=np.float32)

        # 호모그래피 계산 (RANSAC 알고리즘 적용)
        # 2.0~5.0 사이에서 최적 값 실험
        H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 3.0)
        self.homography_mat = H

    def plc_control(self, address, mode):
        # if self.client.write_single_register(address, mode):
        #     print(f'{address} 주소 쓰기 성공: {mode}')
        # else:
        #     print(f'{address} 주소 쓰기 실패')
        print(f'{address} 주소 쓰기 성공: {mode}')
