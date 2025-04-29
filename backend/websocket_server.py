import websockets
import asyncio


class WebsocketServer:
    def __init__(self):
        print('Initialize Completed')

    async def handle_connection(self, websocket):
        print('클라이언트 연결 성공')
        try:
            async for message in websocket:
                print(message)
        except websockets.exceptions.ConnectionClosed as e:
            if e.code == 1000:
                print('클라이언트 정상적으로 연결 종료')
            else:
                print(f'클라이언트 비정상적으로 연결 종료: {e.code}')

    async def run(self):
        async with websockets.serve(lambda websocket: self.handle_connection(websocket), 'localhost', 8765):
            await asyncio.Future()


if __name__ == '__main__':
    websocket_server = WebsocketServer()
    asyncio.run(websocket_server.run())
