# File: app/models/processed_video.py
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.user import PyObjectId

class ProcessedVideoModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    video_id: PyObjectId
    file_path: Optional[str] = None  # Đường dẫn lưu video đã xử lý
    output_url: Optional[str] = None  # URL để truy cập video đã xử lý
    created_at: datetime = Field(default_factory=datetime.now)
    processing_start_time: Optional[datetime] = None
    processing_end_time: Optional[datetime] = None
    status: str = "completed"  # 'completed', 'failed'
    error_message: Optional[str] = None  # Nếu có lỗi xảy ra
    size: Optional[int] = None  # kích thước file sau xử lý (bytes)
    duration: Optional[int] = None  # thời lượng video sau xử lý (tính bằng giây)
    metadata: Optional[Dict[str, Any]] = None  # Thông tin thêm về video đã xử lý
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "status": "completed",
                "size": 15000000,
                "duration": 120,
                "metadata": {"resolution": "1080p", "format": "mp4"}
            }
        }