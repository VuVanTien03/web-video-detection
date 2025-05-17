# File: app/services/video_service.py

from app.database import video_collection, processed_video_collection, user_collection
from bson import ObjectId
from datetime import datetime
import os
from fastapi import HTTPException, status, Depends, BackgroundTasks
from app.utils.security import get_current_active_user
from app.config import settings
import cv2
import app.utils.setup_path_yolo
from models.common import DetectMultiBackend, AutoShape
from fastapi import BackgroundTasks, HTTPException, Depends
from fastapi.responses import StreamingResponse
import torch
import queue
import threading
import numpy as np
import time
import json
from pathlib import Path

async def get_video_by_id(video_id):
    """
    Lấy thông tin video theo id
    """
    if not ObjectId.is_valid(video_id):
        return None
    
    video = await video_collection.find_one({"_id": ObjectId(video_id)})
    return video

async def get_processed_video_by_video_id(video_id):
    """
    Lấy thông tin video đã xử lý theo id video gốc
    """
    if not ObjectId.is_valid(video_id):
        return None
    
    processed_video = await processed_video_collection.find_one({"video_id": ObjectId(video_id)})
    return processed_video

async def get_user_videos(user_id, skip=0, limit=10):
    """
    Lấy danh sách video của người dùng
    """
    videos = []
    cursor = video_collection.find(
        {"user_id": ObjectId(user_id)}
    ).sort("upload_date", -1).skip(skip).limit(limit)
    
    async for video in cursor:
        videos.append(video)
    
    return videos

async def get_all_videos(user_id):
    """
    get all videos of user 
    """
    videos = []
    cursor = video_collection.find(
        {"user_id": ObjectId(user_id)}
    )
    
    async for video in cursor:
        videos.append(video)
    return videos 

async def delete_video(video_id, user_id, is_admin=False):
    """
    Xóa video
    """
    if not ObjectId.is_valid(video_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video ID"
        )
    
    # Lấy thông tin video
    video = await video_collection.find_one({"_id": ObjectId(video_id)})
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Kiểm tra quyền
    if str(video["user_id"]) != str(user_id) and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Xóa file video gốc nếu có
    if video.get("file_path") and os.path.exists(video["file_path"]):
        os.remove(video["file_path"])
    
    # Lấy thông tin video đã xử lý
    processed_video = await processed_video_collection.find_one({"video_id": ObjectId(video_id)})
    
    # Xóa file video đã xử lý nếu có
    if processed_video and processed_video.get("file_path") and os.path.exists(processed_video["file_path"]):
        os.remove(processed_video["file_path"])
    
    # Xóa thông tin video đã xử lý trong database
    if processed_video:
        await processed_video_collection.delete_one({"_id": processed_video["_id"]})
    
    # Xóa thông tin video gốc trong database
    await video_collection.delete_one({"_id": ObjectId(video_id)})
    
    return True

async def get_path_video(video_id, user=Depends(get_current_active_user)):
    """
    Lấy đường dẫn file video
    """
    if not ObjectId.is_valid(video_id):
        raise HTTPException(status_code=400, detail="Invalid video ID")
    
    object_id = ObjectId(video_id)
    user_id = user["_id"]
    
    # Lấy thông tin video
    video = await video_collection.find_one({"_id": object_id, "user_id": ObjectId(user_id)})
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video['file_path']

# Đường dẫn tuyệt đối từ thư mục gốc của project
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_WEIGHTS_PATH = BASE_DIR / "services" / "gelan_t.pt"

# Lớp Buffer khung ảnh với khả năng quản lý hiệu quả
class FrameBuffer:
    _instance = None
    
    @classmethod
    def get_buffer(cls, max_size=5):
        if cls._instance is None:
            cls._instance = FrameBuffer(max_size)
        return cls._instance
    
    def __init__(self, max_size=5):
        self.input_frames = queue.Queue(maxsize=max_size)
        self.processed_frames = queue.Queue(maxsize=max_size)
        self.latest_result = None
        self.processing = True
        self.lock = threading.Lock()
        # Lưu trữ phát hiện bạo lực theo thời gian
        self.violence_detections = []
        # Theo dõi thời điểm bạo lực mới nhất để tránh lặp ghi
        self.last_violence_time = -5  # Seconds
        # Lưu trữ các kết quả phát hiện
        self.detections = []

    def put_input(self, frame):
        # Nếu queue đầy, loại bỏ frame cũ nhất
        if self.input_frames.full():
            try:
                self.input_frames.get_nowait()
            except queue.Empty:
                pass
        try:
            self.input_frames.put(frame, block=False)
        except queue.Full:
            pass

    def get_input(self):
        try:
            return self.input_frames.get(block=True, timeout=0.1)
        except queue.Empty:
            return None

    def put_processed(self, frame, detection):
        """Lưu frame đã xử lý cùng kết quả phát hiện"""
        # Nếu queue đầy, loại bỏ frame cũ nhất
        if self.processed_frames.full():
            try:
                self.processed_frames.get_nowait()
            except queue.Empty:
                pass
        try:
            self.processed_frames.put((frame, detection), block=False)
        except queue.Full:
            pass

    def get_processed_frame(self):
        """Lấy frame đã được xử lý"""
        return self.processed_frames.get(block=False)

    def put_detections(self, detection_data):
        """Lưu thông tin phát hiện"""
        with self.lock:
            self.detections.append(detection_data)

    def put_result(self, frame, detection, timestamp=None):
        """Lưu kết quả mới nhất"""
        with self.lock:
            self.latest_result = (frame, detection, timestamp)

    def get_latest(self):
        """Lấy kết quả mới nhất"""
        with self.lock:
            return self.latest_result

    def record_violence(self, timestamp, confidence, box):
        """Ghi lại thời điểm phát hiện bạo lực"""
        with self.lock:
            # Chỉ ghi lại nếu cách lần ghi cuối ít nhất 1 giây
            if timestamp - self.last_violence_time >= 1.0:
                self.violence_detections.append({
                    "timestamp": timestamp,
                    "time_str": self.format_time(timestamp),
                    "confidence": float(confidence),
                    "box": [int(b) for b in box]
                })
                self.last_violence_time = timestamp

    def get_violence_detections(self):
        """Lấy danh sách các phát hiện bạo lực"""
        with self.lock:
            return self.violence_detections.copy()

    @staticmethod
    def format_time(seconds):
        """Chuyển đổi số giây thành định dạng MM:SS"""
        minutes = int(seconds / 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def stop(self):
        """Dừng xử lý"""
        self.processing = False

# Hàm YOLO worker (xử lý ảnh)
def yolo_worker(model, frame_buffer, conf_threshold=0.5):
    while frame_buffer.processing:
        frame = frame_buffer.get_input()
        if frame is None:
            time.sleep(0.01)  # Ngủ một chút để tránh tiêu tốn CPU
            continue

        with torch.no_grad():
            # Thực hiện dự đoán YOLO trên frame
            predictions = model(frame)
            frame_buffer.put_processed(frame, predictions)

def show_video_stream(video_path, model, device="cpu"):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_time = 1.0 / fps if fps > 0 else 0.03

    # Khởi tạo buffer và worker threads
    frame_buffer = FrameBuffer.get_buffer()
    
    # Khởi động worker thread
    worker_thread = threading.Thread(
        target=yolo_worker,
        args=(model, frame_buffer, 0.8),
        daemon=True
    )
    worker_thread.start()

    def generate():
        frame_count = 0
        last_time = time.time()

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                current_time = time.time()
                elapsed = current_time - last_time
                # tính thời gian hiện tại của video
                current_video_time = frame_count/fps if fps > 0 else 0
                
                # Đưa frame vào để xử lý
                frame_buffer.put_input(frame.copy())

                # Lấy kết quả mới nhất đã xử lý
                result = None
                try:
                    result = frame_buffer.get_processed_frame()
                except queue.Empty:
                    pass
                
                detections = []
                if result:
                    processed_frame, predictions = result
                    timestamp = frame_count/fps if fps > 0 else 0
                    
                    # Lưu phát hiện vào buffer
                    frame_buffer.put_detections((predictions, timestamp))

                    # Vẽ các hộp giới hạn và nhãn
                    if len(predictions.pred) > 0:
                        for det in predictions.pred[0]:
                            x1, y1, x2, y2, conf, class_id = det[:6]
                            if conf < 0.8:
                                continue
                                
                            detections.append({
                                "time": float(current_video_time),
                                "confidence": float(conf),
                                "bounding_box": [float(x1), float(y1), float(x2), float(y2)],
                                "label": "violence"
                            })

                            # Ghi lại phát hiện bạo lực
                            frame_buffer.record_violence(current_video_time, conf, [x1, y1, x2, y2])

                            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                            label = "violence"
                            conf_str = f"{conf:.2f}"

                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 4)
                            cv2.putText(frame, label, (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                            cv2.putText(frame, conf_str, (x1, y1 - 25),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Gửi thông tin phát hiện khi có và mỗi 1000 frame
                if detections and frame_count % 1000 == 0:
                    yield (
                        b'--frame\r\n'
                        b'Content-Type: application/json\r\n\r\n' +
                        json.dumps({"detections": detections}).encode() + b'\r\n'
                    )
                
                # Hiển thị FPS
                fps_text = f"FPS: {1.0 / elapsed:.1f}" if elapsed > 0 else "FPS: -"
                cv2.putText(frame, fps_text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Cập nhật thời gian cho frame tiếp theo
                last_time = current_time

                # Encode frame thành JPEG với chất lượng tốt hơn
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                ret, buffer = cv2.imencode('.jpg', frame, encode_param)
                frame_bytes = buffer.tobytes()

                # Gửi frame đến client
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                # Kiểm soát frame rate để tránh quá tải CPU
                processing_time = time.time() - current_time
                sleep_time = max(0, frame_time - processing_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        finally:
            # Đảm bảo dọn dẹp tài nguyên
            frame_buffer.stop()
            cap.release()

    return StreamingResponse(
        generate(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

async def track_video_service(video_id, weights_path=DEFAULT_WEIGHTS_PATH, device=None):
    # Xác định thiết bị phù hợp
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Tìm video trong database
    video = await video_collection.find_one({"_id": ObjectId(video_id)})

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = video["file_path"]

    # Kiểm tra xem file video có tồn tại
    if not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found on server")

    # Load model YOLO
    try:
        model_backend = DetectMultiBackend(weights=str(weights_path), device=device)
        model = AutoShape(model_backend)
        model.eval()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

    # Trả về stream video
    return show_video_stream(video_path, model, device=device)

import asyncio
async def get_detection():
    frame_buffer = FrameBuffer.get_buffer()
    
    async def detection_stream():
        last_index = 0
        while frame_buffer.processing:
            with frame_buffer.lock:
                detections = frame_buffer.detections
                
            if len(detections) > last_index:
                new_detections = detections[last_index:]
                last_index = len(detections)
                
                yield(
                    b'--frame\r\n'
                    b'Content-Type: application/json\r\n\r\n' +
                    json.dumps({"detections": new_detections}).encode() + b'\r\n'
                )
            await asyncio.sleep(0.1)
            
    return StreamingResponse(detection_stream(), media_type="multipart/x-mixed-replace; boundary=frame")