# app/schemas/upload_video_response.py
from pydantic import BaseModel
from app.schemas.video import VideoResponse

class UploadVideoResponse(BaseModel):
    video: VideoResponse
