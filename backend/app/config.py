import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings  
load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "Video Processing API"
    API_V1_STR: str = "/api/v1"

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))

    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL", "")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "")

    # File storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    PROCESSED_DIR: str = os.getenv("PROCESSED_DIR", "./processed")

    # Video processing
    MAX_VIDEO_SIZE: int = 1024 * 1024 * 500
    ALLOWED_VIDEO_TYPES: list = ["mp4", "avi", "mov", "mkv", "webm"]

settings = Settings()
