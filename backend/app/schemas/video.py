# File: app/schemas/video.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime

class VideoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None

class VideoCreateLocal(VideoBase):
    # Server sẽ tự động sinh ra thông tin này khi người dùng tải lên file
    source_type: str = "local"

class VideoCreateUrl(VideoBase):
    url: HttpUrl
    source_type: str = "url"

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class VideoInDB(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    original_filename: Optional[str] = None
    file_path: Optional[str] = None
    url: Optional[str] = None
    source_type: str
    upload_date: datetime
    duration: Optional[int] = None
    size: Optional[int] = None
    status: str
    
    class Config:
        schema_extra = {
            "example": {
                "id": "60d21b4967d0d8992e610c85",
                "user_id": "60d21b4967d0d8992e610c85",
                "title": "My First Video",
                "description": "A video about programming",
                "original_filename": "tutorial.mp4",
                "file_path": "/uploads/user_60d21b4967d0d8992e610c85/tutorial.mp4",
                "source_type": "local",
                "upload_date": "2021-06-22T12:00:00",
                "duration": 180,
                "size": 25000000,
                "status": "completed"
            }
        }

class VideoResponse(VideoInDB):
    pass