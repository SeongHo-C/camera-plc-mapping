import time
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
        pixel_vec = np.array([x, y, 1], dtype=np.int64)
        plc_vec = self.affine_mat @ pixel_vec

        return round(plc_vec[0]), round(plc_vec[1])

    def calculate_affine_matrix(self, mapping_items):
        converted = {key: [tuple(coord) for coord in coords] for key, coords in mapping_items.items()}
        pixel_pts = converted['Pixel']
        plc_pts = converted['PLC']

        # 4개 이상의 대응점으로 아핀 변환 행렬 계산 (최소제곱법)
        A = []
        B = []

        for (x, y), (X, Y) in zip(pixel_pts, plc_pts):
            A.append([x, y, 1, 0, 0, 0])
            A.append([0, 0, 0, x, y, 1])
            B.extend([X, Y])

        A = np.array(A)
        B = np.array(B)

        # 최소제곱법으로 파라미터 추정
        params = np.linalg.lstsq(A, B, rcond=None)[0]
        a, b, c, d, e, f = params

        # 3x3 아핀 변환 행렬 구성
        self.affine_mat = np.array([
            [a, b, c],
            [d, e, f],
            [0, 0, 1]
        ])

    def plc_control(self, address, mode):
        # if self.client.write_single_register(address, mode):
        #     print(f'{address} 주소 쓰기 성공: {mode}')
        # else:
        #     print(f'{address} 주소 쓰기 실패')
        print(f'{address} 주소 쓰기 성공: {mode}')
