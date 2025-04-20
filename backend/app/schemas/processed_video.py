# File: app/schemas/processed_video.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ProcessedVideoCreate(BaseModel):
    video_id: str
    file_path: Optional[str] = None
    output_url: Optional[str] = None
    
class ProcessedVideoUpdate(BaseModel):
    file_path: Optional[str] = None
    output_url: Optional[str] = None
    processing_end_time: Optional[datetime] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    size: Optional[int] = None
    duration: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class ProcessedVideoInDB(BaseModel):
    id: str
    video_id: str
    file_path: Optional[str] = None
    output_url: Optional[str] = None
    created_at: datetime
    processing_start_time: Optional[datetime] = None
    processing_end_time: Optional[datetime] = None
    status: str
    error_message: Optional[str] = None
    size: Optional[int] = None
    duration: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "60d21b4967d0d8992e610c85",
                "video_id": "60d21b4967d0d8992e610c85",
                "file_path": "/processed/user_60d21b4967d0d8992e610c85/tutorial_processed.mp4",
                "output_url": "https://example.com/videos/tutorial_processed.mp4",
                "created_at": "2021-06-22T12:00:00",
                "processing_start_time": "2021-06-22T12:01:00",
                "processing_end_time": "2021-06-22T12:05:00",
                "status": "completed",
                "size": 15000000,
                "duration": 180,
                "metadata": {"resolution": "1080p", "format": "mp4"}
            }
        }

class ProcessedVideoResponse(ProcessedVideoInDB):
    pass