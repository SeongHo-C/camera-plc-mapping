import websockets
import asyncio
import json
from camera.basic import BasicCamera
from camera.depth import DepthCamera
from plc_controller import PlcController
from utils import save_json, load_json


class WebsocketServer:
    def __init__(self):
        self.plc_controller = PlcController()
        self.camera = DepthCamera(self.plc_controller)

    async def handle_message(self, websocket, message):
        # 문자열로 된 JSON 데이터를 사전처럼 사용
        data = json.loads(message)
        command_type = data['type']
        command_action = data['action']
        command_data = data.get('data')

        if command_type == 'camera':
            if command_action == 'start':
                if self.camera.initialize():
                    # asyncio 라이브러리에서 비동기 코드를 동시적으로 실행하기 위해 사용
                    asyncio.create_task(self.camera.streaming(websocket))
            elif command_action == 'capture':
                filename = self.camera.capture_frame()
                await websocket.send(json.dumps({
                    'type': 'message',
                    'message': f'캡처 완료: {filename}'
                }))

        elif command_type == 'shoot':
            if command_action == 'manual':
                mode = command_data['mode']
                x = command_data['x']
                y = command_data['y']

                plc_x, plc_y = self.plc_controller.manual_shoot(mode, x, y)
                await websocket.send(json.dumps({
                    'type': 'message',
                    'message': f'수동 사격 완료: ({plc_x}, {plc_y})'
                }))
            elif command_action == 'continuous':
                targets = self.plc_controller.continuous_shoot(command_data)
                await websocket.send(json.dumps({
                    'type': 'message',
                    'message': f'연속 사격 완료: {targets}'
                }))

        elif command_type == 'mapping':
            if command_action == 'save':
                save_json('data/mapping_items.json', command_data)
                await websocket.send(json.dumps({
                    'type': 'message',
                    'message': 'PLC, Pixel 매핑 좌표 저장하기'
                }))
            elif command_action == 'load':
                await load_json('data/mapping_items.json', websocket)
                await websocket.send(json.dumps({
                    'type': 'message',
                    'message': 'PLC, Pixel 매핑 좌표 불러오기'
                }))
            elif command_action == 'mapping':
                self.plc_controller.calculate_homography_matrix(command_data)
                await websocket.send(json.dumps({
                    'type': 'message',
                    'message': '아핀 변환 행렬 구성'
                }))
            elif command_action == 'validation':
                max_error, avg_error = self.plc_controller.validate_mapping()
                await websocket.send(json.dumps({
                    'type': 'message',
                    'message': f'최대 오차: {max_error}, 평균 오차: {avg_error}'
                }))

        elif command_type == 'control':
            if command_action == 'shootMode':
                self.plc_controller.plc_control(1800, command_data)
                await websocket.send(json.dumps({
                    'type': 'message',
                    'message': f'현재 사격 모드: {"ON" if command_data == 1 else "OFF"}'
                }))
            elif command_action == 'laserMode':
                mode = command_data['mode']
                correction_value = command_data['correctionValue']

                self.plc_controller.plc_control(1805, mode)
                if mode == 1:
                    self.plc_controller.laser_correction_value = correction_value
                await websocket.send(json.dumps({
                    'type': 'message',
                    'message': f'현재 레이저 모드: {"ON" if mode == 1 else "OFF"}'
                }))
            elif command_action == 'detectMode':
                self.camera.detect_mode = command_data
                await websocket.send(json.dumps({
                    'type': 'message',
                    'message': f'현재 인식 모드: {"ON" if command_data == 1 else "OFF"}'
                }))

    async def handle_connection(self, websocket):
        print('클라이언트 연결 성공')
        try:
            # 클라이언트가 보낸 메시지를 지속적으로 수신
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed as e:
            if e.code == 1000:
                print('클라이언트 정상적으로 연결 종료')
            else:
                print(f'클라이언트 비정상적으로 연결 종료: {e.code}')

    async def run(self):
        async with websockets.serve(lambda websocket: self.handle_connection(websocket), 'localhost', 8765):
            # 서버가 종료되지 않도록 설정
            await asyncio.Future()


if __name__ == '__main__':
    websocket_server = WebsocketServer()
    # 비동기로 실행
    asyncio.run(websocket_server.run())
