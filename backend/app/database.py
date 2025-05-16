# File: app/database.py
import motor.motor_asyncio
from app.config import settings

client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
database = client[settings.DATABASE_NAME]

user_collection = database.get_collection("users")
video_collection = database.get_collection("videos")
processed_video_collection = database.get_collection("processed_videos")