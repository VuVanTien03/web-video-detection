# File: app/services/video_service.py
from app.database import video_collection, processed_video_collection
from bson import ObjectId
from datetime import datetime
import os
from fastapi import HTTPException, status

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