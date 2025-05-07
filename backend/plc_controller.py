import time
from pyModbusTCP.client import ModbusClient


class PlcController:
    def __init__(self):
        self.client = ModbusClient(host='192.168.1.10', port=502)

        if self.client.open():
            self.client.write_single_register(1800, 0)  # 발사
            # time.sleep(0.05)
            self.client.write_single_register(1805, 0)  # 레이저

    def manual_shoot(self, mode, x, y):
        if mode == 'PLC':
            # 연속된 주소(1500, 1501)로 변경 희망, 하나의 주소만을 쓰더라도 사격이 되는지 확인 필요
            # self.client.write_multiple_registers(1500, [int(x), int(y)])

            """
            if self.client.write_single_register(1500, int(x)):
                self.client.write_single_register(1600, int(y))
                print(f'PLC 좌표 쓰기 성공: {x}, {y}')
            else:
                print('PLC 좌표 쓰기 실패')
            """
            print(f'PLC 좌표 쓰기 성공: {x}, {y}')

    def continuous_shoot(self, corner):
        for coordinate in corner:
            x = int(coordinate['x'])
            y = int(coordinate['y'])

            # if self.client.write_single_register(1500, x):
            #     self.client.write_single_register(1600, y)
            #     print(f'PLC 좌표 쓰기 성공: {x}, {y}')
            # else:
            #     print(f'PLC 좌표 쓰기 실패: {x}, {y}')
            print(f'PLC 좌표 쓰기 성공: {x}, {y}')
            time.sleep(2)
