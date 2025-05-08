# File: app/services/video_service.py

from app.database import video_collection, processed_video_collection , user_collection
from bson import ObjectId
from datetime import datetime
import os
from fastapi import HTTPException, status , Depends , BackgroundTasks
from app.utils.security import get_current_active_user
from app.config import settings
import cv2
import app.utils.setup_path_yolo
from models.common import DetectMultiBackend, AutoShape
from fastapi import  BackgroundTasks, HTTPException, Depends
from fastapi.responses import StreamingResponse
import torch
# from deep_sort_realtime.deepsort_tracker import DeepSort
import queue
import threading
import numpy as np
import time 
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
    get all videos of use 
    """
    videos = []
    cursor = video_collection.find(
        {"user_id" : ObjectId(user_id)}
    )
    for video in cursor : 
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
async def get_path_video(video_id , user = Depends(get_current_active_user)) :
    if ObjectId.is_valid(video_id ):
        object_id = ObjectId(video_id)
    user_id = user["_id"]
    videos = get_all_videos(user_id)
    user_upload_dir = os.path.join(settings.UPLOAD_DIR, f"user_{user_id}")
    video_ids = [i["_id"] for i in videos]
    if video_id in video_ids : 
        video = await video_collection.find_one({'_id':ObjectId(video_id)})
        return video['file_path']
    else : 
        raise HTTPException(status_code = 400 , detail = "not found")
# async def yolo_warm():



# # Hàm YOLO worker (xử lý ảnh từng frame)
# def yolo_worker(model, image_stack, result):
#     while True:
#         if not image_stack.empty():
#             frame = image_stack.get()
#             with torch.no_grad():
#                 # Thực hiện dự đoán YOLO trên frame
#                 predictions = model(frame)
#                 result.put(predictions)  # Đưa kết quả vào queue
#
#
# def show_video_stream(video_path, image_stack, result):
#     cap = cv2.VideoCapture(video_path)
#     fps = cap.get(cv2.CAP_PROP_FPS)
#     delay_time = 1 / fps if fps > 0 else 0.03
#
#     def generate():
#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break
#             image_stack.put(frame)
#
#             if not result.empty():
#                 pre = result.get().pred[0]
#                 for det in pre:
#                     x1, y1, x2, y2, conf, class_id = det[:6]
#                     x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
#                     if conf < 0.8:
#                         continue
#                     label = "violence"
#                     conf_str = f"{conf:.2f}"
#                     cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 4)
#                     cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
#                     cv2.putText(frame, conf_str, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
#
#             # Encode frame thành JPEG
#             ret, buffer = cv2.imencode('.jpg', frame)
#             frame_bytes = buffer.tobytes()
#
#             # Yield frame với định dạng multipart
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
#
#             time.sleep(delay_time)
#
#         cap.release()
#
#     return StreamingResponse(generate(), media_type='multipart/x-mixed-replace; boundary=frame')
#
#
#
#
# from pathlib import Path
#
# # Đường dẫn tuyệt đối từ thư mục gốc của project
# BASE_DIR = Path(__file__).resolve().parent.parent  # app/services/ => lên backend/app
# DEFAULT_WEIGHTS_PATH = BASE_DIR / "services" / "gelan_t.pt"
#
# async def track_video_service(video_id, weights_path=DEFAULT_WEIGHTS_PATH, device=torch.device("cpu")):
#     video = await video_collection.find_one({"_id": ObjectId(video_id)})
#
#     if not video:
#         raise ValueError("Video not found")
#
#     video_path = video["file_path"]
#
#     # Load model YOLO
#     model_backend = DetectMultiBackend(weights=str(weights_path), device=device)
#     model = AutoShape(model_backend)
#     model.eval()
#
#     result = queue.Queue()
#     image_stack = queue.LifoQueue()
#
#     # Chạy YOLO worker
#     threading.Thread(target=yolo_worker, args=(model, image_stack, result), daemon=True).start()
#
#     # Trả về stream
#     return show_video_stream(video_path, image_stack, result)
# # http://127.0.0.1:8000/api/v1/videos/track_video/681c445031bb616d2342388f
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import cv2
import torch
import threading
import queue
import time
import numpy as np
from pathlib import Path
# from models.common import DetectMultiBackend, AutoShape
from bson import ObjectId
from typing import List, Dict, Any
import json

# Đường dẫn tuyệt đối từ thư mục gốc của project
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_WEIGHTS_PATH = BASE_DIR / "services" / "gelan_t.pt"


# Lớp Buffer khung ảnh với khả năng quản lý hiệu quả hơn và lưu trữ thông tin về hành vi bạo lực
class FrameBuffer:
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

    def put_result(self, frame, detection, timestamp=None):
        with self.lock:
            self.latest_result = (frame, detection, timestamp)

    def get_latest(self):
        with self.lock:
            return self.latest_result

    def record_violence(self, timestamp, confidence, box):
        """Ghi lại thời điểm phát hiện bạo lực"""
        with self.lock:
            # Chỉ ghi lại nếu cách lần ghi cuối ít nhất 1 giây
            if timestamp - self.last_violence_time >= 1.0:
                self.violence_detections.append({
                    "timestamp": timestamp,  # Thời điểm (giây)
                    "time_str": self.format_time(timestamp),  # Định dạng thời gian dễ đọc
                    "confidence": float(confidence),  # Độ tin cậy
                    "box": [int(b) for b in box]  # Tọa độ bounding box
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
        self.processing = False


# Hàm YOLO worker (xử lý ảnh)
def yolo_worker(model, frame_buffer, conf_threshold=0.5):
    while frame_buffer.processing:
        frame_data = frame_buffer.get_input()
        if frame_data is None:
            time.sleep(0.01)  # Ngủ một chút để tránh tiêu tốn CPU
            continue

        frame, timestamp = frame_data  # Nhận frame và timestamp

        with torch.no_grad():
            # Thực hiện dự đoán YOLO trên frame
            predictions = model(frame)
            frame_buffer.put_result(frame, predictions, timestamp)


def show_video_stream(video_path, model, device="cpu", return_timestamps=False):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_time = 1.0 / fps if fps > 0 else 0.03
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Khởi tạo buffer và worker threads
    frame_buffer = FrameBuffer(max_size=3)

    # Khởi động 1 worker thread (có thể tăng lên nếu GPU hỗ trợ)
    worker_thread = threading.Thread(
        target=yolo_worker,
        args=(model, frame_buffer, 0.8),
        daemon=True
    )
    worker_thread.start()

    def generate():
        frame_count = 0
        start_time = time.time()
        last_time = start_time

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                current_time = time.time()
                elapsed = current_time - last_time

                # Tính thời gian video hiện tại
                current_video_time = frame_count / fps if fps > 0 else frame_count * 0.03

                # Đưa frame và timestamp vào để xử lý
                frame_buffer.put_input((frame.copy(), current_video_time))

                # Lấy kết quả mới nhất đã xử lý
                result = frame_buffer.get_latest()
                if result:
                    processed_frame, predictions, timestamp = result

                    # Vẽ các hộp giới hạn và nhãn
                    if len(predictions.pred) > 0 and len(predictions.pred[0]) > 0:
                        for det in predictions.pred[0]:
                            x1, y1, x2, y2, conf, class_id = det[:6]
                            if conf < 0.8:
                                continue

                            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                            label = "violence"
                            conf_str = f"{conf:.2f}"

                            # Ghi lại thời điểm phát hiện bạo lực
                            frame_buffer.record_violence(
                                timestamp,
                                conf,
                                [x1, y1, x2, y2]
                            )

                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Màu đỏ cho bạo lực
                            cv2.putText(frame, label, (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                            cv2.putText(frame, conf_str, (x1, y1 - 25),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                # Hiển thị thông tin phụ trên video
                fps_text = f"FPS: {1.0 / elapsed:.1f}" if elapsed > 0 else "FPS: -"
                timestamp_text = f"Time: {frame_buffer.format_time(current_video_time)}"
                progress_text = f"Progress: {frame_count}/{total_frames}"

                cv2.putText(frame, fps_text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, timestamp_text, (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, progress_text, (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Số lượng sự kiện bạo lực đã phát hiện
                violence_count = len(frame_buffer.get_violence_detections())
                cv2.putText(frame, f"Violence detected: {violence_count}", (10, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

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
            detections = frame_buffer.get_violence_detections()
            frame_buffer.stop()
            cap.release()

            # Nếu hàm được gọi với return_timestamps=True, trả về kết quả
            if return_timestamps:
                return detections

    # Trả về stream video
    return StreamingResponse(
        generate(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )


async def track_video_service(video_id, weights_path=DEFAULT_WEIGHTS_PATH, device=None):
    """
    Dịch vụ theo dõi video để phát hiện bạo lực
    """
    # Xác định thiết bị phù hợp
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Tìm video trong database
    # from database import video_collection  # Giả sử có import này
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


async def get_violence_timestamps(video_id, weights_path=DEFAULT_WEIGHTS_PATH, device=None):
    """
    Phân tích video và trả về danh sách các thời điểm phát hiện bạo lực
    """
    # Xác định thiết bị phù hợp
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Tìm video trong database
    from database import video_collection  # Giả sử có import này
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

    # Khởi tạo các biến cần thiết
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="Could not open video file")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_time = 1.0 / fps if fps > 0 else 0.03
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Khởi tạo buffer và worker threads
    frame_buffer = FrameBuffer(max_size=3)

    # Khởi động worker thread
    worker_thread = threading.Thread(
        target=yolo_worker,
        args=(model, frame_buffer, 0.8),
        daemon=True
    )
    worker_thread.start()

    try:
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # Tính thời gian video hiện tại
            current_video_time = frame_count / fps if fps > 0 else frame_count * 0.03

            # Đưa frame và timestamp vào để xử lý
            frame_buffer.put_input((frame.copy(), current_video_time))

            # Lấy kết quả mới nhất đã xử lý
            result = frame_buffer.get_latest()
            if result:
                processed_frame, predictions, timestamp = result

                # Tìm các hành vi bạo lực
                if len(predictions.pred) > 0 and len(predictions.pred[0]) > 0:
                    for det in predictions.pred[0]:
                        x1, y1, x2, y2, conf, class_id = det[:6]
                        if conf < 0.8:
                            continue

                        # Ghi lại thời điểm phát hiện bạo lực
                        frame_buffer.record_violence(
                            timestamp,
                            conf,
                            [int(x1), int(y1), int(x2), int(y2)]
                        )

            # In tiến trình để theo dõi
            if frame_count % 100 == 0:
                print(f"Processing: {frame_count}/{total_frames} frames ({frame_count / total_frames * 100:.1f}%)")

            # Kiểm soát tốc độ xử lý nếu cần
            time.sleep(0.001)  # Cho phép các thread khác chạy

    finally:
        # Lấy danh sách các phát hiện bạo lực
        violence_detections = frame_buffer.get_violence_detections()

        # Đảm bảo dọn dẹp tài nguyên
        frame_buffer.stop()
        cap.release()

    # Sắp xếp các phát hiện theo thời gian
    violence_detections.sort(key=lambda x: x["timestamp"])

    # Trả về kết quả
    return {
        "video_id": video_id,
        "video_path": video_path,
        "total_frames": total_frames,
        "fps": fps,
        "duration": total_frames / fps if fps > 0 else 0,
        "violence_count": len(violence_detections),
        "violence_detections": violence_detections
    }

# API endpoint (đã có sẵn trong FastAPI app của bạn)
# @app.get("/api/v1/videos/track_video/{video_id}")
# async def track_video(video_id: str):
#     return await track_video_service(video_id)

# API endpoint mới để lấy danh sách các thời điểm bạo lực
# @app.get("/api/v1/videos/violence_timestamps/{video_id}")
# async def violence_timestamps(video_id: str):
#     return await get_violence_timestamps(video_id)