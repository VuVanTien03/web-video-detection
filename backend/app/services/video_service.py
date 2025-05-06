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
from deep_sort_realtime.deepsort_tracker import DeepSort
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



# Hàm YOLO worker (xử lý ảnh từng frame)
def yolo_worker(model, image_stack, result):
    while True:
        if not image_stack.empty():
            frame = image_stack.get()
            # Thực hiện dự đoán YOLO trên frame
            predictions = model(frame)
            result.put(predictions)  # Đưa kết quả vào queue


def show_video_stream(video_path, image_stack, result):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    delay_time = 1 / fps if fps > 0 else 0.03

    def generate():
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            image_stack.put(frame)

            if not result.empty():
                pre = result.get().pred[0]
                for det in pre:
                    x1, y1, x2, y2, conf, class_id = det[:6]
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                    if conf < 0.8:
                        continue
                    label = "violence"
                    conf_str = f"{conf:.2f}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    cv2.putText(frame, conf_str, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Encode frame thành JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            # Yield frame với định dạng multipart
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(delay_time)

        cap.release()

    return StreamingResponse(generate(), media_type='multipart/x-mixed-replace; boundary=frame')




from pathlib import Path

# Đường dẫn tuyệt đối từ thư mục gốc của project
BASE_DIR = Path(__file__).resolve().parent.parent  # app/services/ => lên backend/app
DEFAULT_WEIGHTS_PATH = BASE_DIR / "services" / "gelan_t.pt"

async def track_video_service(video_id, weights_path=DEFAULT_WEIGHTS_PATH, device=torch.device("cpu")):
    video = await video_collection.find_one({"_id": ObjectId(video_id)})

    if not video:
        raise ValueError("Video not found")

    video_path = video["file_path"]

    # Load model YOLO
    model_backend = DetectMultiBackend(weights=str(weights_path), device=device)
    model = AutoShape(model_backend)
    model.eval()

    result = queue.Queue()
    image_stack = queue.LifoQueue()

    # Chạy YOLO worker
    threading.Thread(target=yolo_worker, args=(model, image_stack, result), daemon=True).start()

    # Trả về stream
    return show_video_stream(video_path, image_stack, result)
