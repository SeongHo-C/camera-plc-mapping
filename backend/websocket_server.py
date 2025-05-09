import websockets
import asyncio
import json
from camera import Camera
from plc_controller import PlcController
from utils import save_json, load_json


class WebsocketServer:
    def __init__(self):
        self.camera = Camera()
        self.plc_controller = PlcController()

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
                    'message': f'캡처가 완료되었습니다.\n파일명: {filename}'
                }))

        elif command_type == 'shoot':
            if command_action == 'manual':
                mode = command_data['mode']
                x = command_data['x']
                y = command_data['y']

                plc_x, plc_y = self.plc_controller.manual_shoot(mode, x, y)
                if mode == 'Pixel':
                    await websocket.send(json.dumps({
                        'type': 'message',
                        'message': f'PLC 좌표로 변경 완료되었습니다.\nPixel: ({x}, {y}) 👉 PLC: ({plc_x}, {plc_y})'
                    }))
            elif command_action == 'continuous':
                self.plc_controller.continuous_shoot(command_data)

        elif command_type == 'mapping':
            if command_action == 'save':
                save_json('data/mapping_items.json', command_data)
            elif command_action == 'load':
                await load_json('data/mapping_items.json', websocket)
            elif command_action == 'mapping':
                self.plc_controller.calculate_affine_matrix(command_data)

        elif command_type == 'control':
            if command_action == 'shootMode':
                self.plc_controller.plc_control(1800, command_data)
            elif command_action == 'laserMode':
                self.plc_controller.plc_control(1805, command_data)

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
