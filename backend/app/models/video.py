# File: app/models/video.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.user import PyObjectId

class VideoModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    title: str
    description: Optional[str] = None
    original_filename: Optional[str] = None
    file_path: Optional[str] = None  # Đường dẫn lưu trữ nếu tải lên từ localhost
    url: Optional[str] = None  # URL nếu người dùng nhập URL video
    source_type: str  # 'local', 'url'
    upload_date: datetime = Field(default_factory=datetime.now)
    duration: Optional[int] = None  # thời lượng video (tính bằng giây)
    size: Optional[int] = None  # kích thước file (bytes)
    status: str = "pending"  # 'pending', 'processing', 'completed', 'failed'
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "title": "My First Video",
                "description": "A video about programming",
                "source_type": "local",
                "status": "pending",
            }
        }