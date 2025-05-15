from collections import deque
import threading
import queue
# Lớp Buffer khung ảnh với khả năng quản lý hiệu quả hơn
class FrameBuffer:
    _buffer = None
    def __init__(self, max_size=5):
        self.input_frames = deque(maxlen=max_size)
        self.processed_frames = queue.Queue()
        self.detection_list = []
        self.latest_result = None
        self.processing = True
        self.lock = threading.Lock()
    @classmethod
    def get_buffer(cls):
        if cls._buffer is None:
            cls._buffer = FrameBuffer()
        return cls._buffer
    def put_input(self, frame):
        self.input_frames.append(frame)

    def get_input(self):
        try:
            return self.input_frames.pop()
        except IndexError:
            return None
    def put_processed(self , frame , detection):
        with self.lock:
            self.processed_frames.put((frame , detection))
    def put_result(self, frame, detection):
        with self.lock:
            self.latest_result = (frame, detection)
    def get_processed_frame(self):
        with self.lock:
            return self.processed_frames.get_nowait()
    def get_latest(self):
        with self.lock:
            return self.latest_result
    def put_detections(self , pre):
        self.detection_list.append(pre)
    def get_detections(self):
        return self.detection_list
    def stop(self):
        self.processing = False