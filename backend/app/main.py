# File: app/main.py
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
import os
import logging
from app.config import settings
from app.routes import user, video, auth
from app.database import database
import aiofiles
import sys 
sys.path.append(r'D:\code\python\DataMining\yolov9')
# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

# Khởi tạo FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="API for video processing service"
)

# Thiết lập CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong môi trường production nên giới hạn origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kiểm tra và tạo thư mục uploads và processed nếu chưa tồn tại
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)

# Đăng ký các router
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(user.router, prefix=settings.API_V1_STR)
app.include_router(video.router, prefix=settings.API_V1_STR)

# Đăng ký thư mục tĩnh cho việc phát video
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/processed", StaticFiles(directory=settings.PROCESSED_DIR), name="processed")

@app.get("/")
async def root():
    return {"message": "Welcome to Video Processing API"}

@app.get(f"{settings.API_V1_STR}/videos/stream/{{user_id}}/{{filename}}")
async def stream_video(user_id: str, filename: str, request: Request):
    """
    Stream video đã xử lý
    """
    video_path = os.path.join(settings.PROCESSED_DIR, f"user_{user_id}", filename)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Đọc file cho streaming
    async def iterfile():
        async with aiofiles.open(video_path, 'rb') as f:
            while chunk := await f.read(8192):  # 8KB chunks
                yield chunk
    
    return StreamingResponse(iterfile(), media_type="video/mp4")

@app.on_event("startup")
async def startup_db_client():
    logger.info("Starting up the application")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("Shutting down the application")

@app.get(f"{settings.API_V1_STR}/test-mongo")
async def test_mongo_connection():
    try:
        collections = await database.list_collection_names()
        return {"status": "success", "collections": collections}
    except Exception as e:
        logger.error(f"MongoDB connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="MongoDB connection failed")