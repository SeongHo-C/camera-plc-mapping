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
            # 연속된 주소(1500, 1501)로 변경 희망
            # self.client.write_multiple_registers(1500, [int(x), int(y)])

            """
            if self.client.write_single_register(1500, int(x)):
                self.client.write_single_register(1600, int(y))
                print(f'PLC 좌표 쓰기 성공: {x}, {y}')
            else:
                print('PLC 좌표 쓰기 실패')
            """
            print(f'PLC 좌표 쓰기 성공: {x}, {y}')


def shoot_plc(self, plc_x, plc_y):
    # 1. X, Y 값 모두 먼저 기록
    x_result = self.client.write_single_register(1500, int(plc_x))
    y_result = self.client.write_single_register(1600, int(plc_y))

    # 2. 둘 다 성공했을 때 트리거 신호
    if x_result and y_result:
        self.client.write_single_register(1700, 1)  # 트리거 신호
        print(f'PLC: X축 {plc_x}, Y축 {plc_y} 사격 트리거')
    else:
        print('PLC: 좌표 쓰기 실패')
