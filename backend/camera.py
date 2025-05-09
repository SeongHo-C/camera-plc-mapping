import cv2
import websockets
import asyncio
import os
import datetime


class Camera:
    def __init__(self):
        self.camera = None
        self.last_frame = None

    def initialize(self):
        try:
            self.camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

            if not self.camera.isOpened():
                raise RuntimeError('카메라를 열 수 없습니다.')

            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            self.camera.set(cv2.CAP_PROP_FPS, 60)

            return True
        except Exception as e:
            print(f'예외 발생: {e}')
            return False

    async def streaming(self, websocket):
        while True:
            try:
                ret, frame = self.camera.read()

                if ret:
                    self.last_frame = frame
                    # 프레임을 JPEG로 인코딩한 뒤 바이너리로 전송
                    _, buffer = cv2.imencode('.jpg', frame)
                    await websocket.send(buffer.tobytes())

                # 프레임 전송 속도 조절
                await asyncio.sleep(0.01667)
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                print(f'예외 발생: {e}')

    def capture_frame(self):
        if self.last_frame is not None:
            save_dir = 'data/captures'
            os.makedirs(save_dir, exist_ok=True)

            filename = datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.jpg'
            cv2.imwrite(os.path.join(save_dir, filename), self.last_frame)

            return filename
