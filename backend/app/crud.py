# File: app/crud.py
from bson import ObjectId
from typing import List, Optional, Dict, Any

from app.database import user_collection, video_collection, processed_video_collection

# User CRUD operations
async def create_user(user_data: dict) -> str:
    result = await user_collection.insert_one(user_data)
    return str(result.inserted_id)

async def get_user(user_id: str) -> Optional[dict]:
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        user["_id"] = str(user["_id"])
    return user

async def get_user_by_email(email: str) -> Optional[dict]:
    user = await user_collection.find_one({"email": email})
    if user:
        user["_id"] = str(user["_id"])
    return user

# Video CRUD operations
async def create_video(video_data: dict) -> str:
    result = await video_collection.insert_one(video_data)
    return str(result.inserted_id)

async def get_video(video_id: str) -> Optional[dict]:
    video = await video_collection.find_one({"_id": ObjectId(video_id)})
    if video:
        video["_id"] = str(video["_id"])
    return video

async def get_videos_by_user(user_id: str) -> List[dict]:
    videos = []
    cursor = video_collection.find({"user_id": user_id})
    async for video in cursor:
        video["_id"] = str(video["_id"])
        videos.append(video)
    return videos

# Processed video CRUD operations
async def create_processed_video(processed_data: dict) -> str:
    result = await processed_video_collection.insert_one(processed_data)
    return str(result.inserted_id)

async def update_processed_video(video_id: str, update_data: Dict[str, Any]) -> bool:
    result = await processed_video_collection.update_one(
        {"_id": ObjectId(video_id)},
        {"$set": update_data}
    )
    return result.modified_count > 0