import cv2
import websockets
import asyncio
import os
import datetime
import pyrealsense2 as rs
import numpy as np
from detection import Detection


class DepthCamera:
    def __init__(self, plc_controller):
        self.detector = Detection(plc_controller)

        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.align = rs.align(rs.stream.color)

        self.last_frame = None
        self.detect_mode = 0

    def initialize(self):
        try:
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

            self.pipeline.start(self.config)
            return True
        except Exception as e:
            print(f'initialize camera: {e}')
            return False

    async def streaming(self, websocket):
        loop = asyncio.get_event_loop()

        while True:
            try:
                frames = self.pipeline.wait_for_frames()
                aligned_frames = self.align.process(frames)

                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()
                frame = np.asanyarray(color_frame.get_data())
                # frame = cv2.flip(frame, -1)

                if self.detect_mode == 1:
                    # 별도 스레드에서 YOLO 추론 실행
                    annotated_frame = await loop.run_in_executor(
                        None,
                        self.detector.detect,
                        frame,
                        depth_frame
                    )
                    self.last_frame = annotated_frame
                else:
                    self.last_frame = frame

                # 프레임을 JPEG로 인코딩한 뒤 바이너리로 전송
                _, buffer = cv2.imencode('.jpg', self.last_frame)
                await websocket.send(buffer.tobytes())

                # 프레임 전송 속도 조절
                await asyncio.sleep(1 / 90)
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
