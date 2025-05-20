
# File: app/routes/video.py
from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, status, BackgroundTasks, Path, Query
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from typing import List, Optional
import os
import aiofiles
import uuid
from app.schemas.video import VideoCreateLocal, VideoCreateUrl, VideoUpdate, VideoResponse
from app.schemas.processed_video import ProcessedVideoResponse
from app.utils.security import get_current_active_user
from app.database import video_collection, processed_video_collection
from app.services.video_processor import process_video
from app.services.video_service import get_video_by_id, get_processed_video_by_video_id, delete_video , track_video_service
from app.utils.validators import validate_video_file_extension, validate_video_size
from datetime import datetime
# from bson import ObjectId
import shutil
from app.config import settings
from app.schemas.upload_video_response import UploadVideoResponse
from fastapi.responses import StreamingResponse
from bson import ObjectId



router = APIRouter(prefix="/videos", tags=["videos"])

@router.post("/upload")  # response_model=VideoResponse
async def upload_video(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user = Depends(get_current_active_user)
):
    if not validate_video_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_VIDEO_TYPES)}"
        )

    # Tạo thư mục lưu video theo người dùng
    user_upload_dir = os.path.join(settings.UPLOAD_DIR, f"user_{str(current_user['_id'])}")
    os.makedirs(user_upload_dir, exist_ok=True)

    # Tạo tên file duy nhất
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(user_upload_dir, unique_filename)

    # Ghi nội dung file
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024 * 1024):
            await out_file.write(content)

    file_size = os.path.getsize(file_path)

    if not validate_video_size(file_size):
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size ({settings.MAX_VIDEO_SIZE / (1024 * 1024)} MB)"
        )

    # Tạo đường dẫn tương đối để public
    relative_path = os.path.relpath(file_path, settings.UPLOAD_DIR).replace("\\", "/")
    public_url = f"http://localhost:8000/api/v1/videos/serve/{relative_path}"

    new_video = {
        "user_id": current_user["_id"],
        "title": title,
        "description": description,
        "original_filename": file.filename,
        "file_path": file_path,
        "video_url": public_url,
        "source_type": "local",
        "upload_date": datetime.now(),
        "size": file_size,
        "status": "pending"
    }

    result = await video_collection.insert_one(new_video)
    video_id = result.inserted_id
    background_tasks.add_task(process_video, str(video_id))
    created_video = await video_collection.find_one({"_id": video_id})

    return {
        "video": {
            "id": str(created_video["_id"]),
            "user_id": str(created_video["user_id"]),
            "title": created_video["title"],
            "description": created_video.get("description"),
            "original_filename": created_video.get("original_filename"),
            "file_path": created_video.get("file_path"),
            "video_url": created_video.get("video_url"),  # Đã đúng public URL
            "source_type": created_video["source_type"],
            "upload_date": created_video["upload_date"],
            "duration": created_video.get("duration"),
            "size": created_video.get("size"),
            "status": created_video["status"]
        }
    }

@router.post("/url", response_model=VideoResponse)
async def create_url_video(
    background_tasks: BackgroundTasks,
    video: VideoCreateUrl,
    current_user = Depends(get_current_active_user)
):
    new_video = {
        "user_id": current_user["_id"],
        "title": video.title,
        "description": video.description,
        "url": str(video.url),
        "source_type": "url",
        "upload_date": datetime.now(),
        "status": "pending"
    }

    result = await video_collection.insert_one(new_video)
    video_id = result.inserted_id
    await process_video(str(video_id))
    created_video = await video_collection.find_one({"_id": video_id})

    return {
        "id": str(created_video["_id"]),
        "user_id": str(created_video["user_id"]),
        "title": created_video["title"],
        "description": created_video.get("description"),
        "original_filename": created_video.get("original_filename"),
        "file_path": created_video.get("file_path"),
        "video_url": created_video.get("video_url") or created_video.get("file_path") or "",  # Đã đúng public URL
        "source_type": created_video["source_type"],
        "upload_date": created_video["upload_date"],
        "duration": created_video.get("duration"),
        "size": created_video.get("size"),
        "status": created_video["status"]
    }




# Thêm code này vào file routers/videos.py hoặc tạo file mới nếu chưa có

# from fastapi import APIRouter, HTTPException, Depends, Path
# from fastapi.responses import FileResponse
# import os
# from typing import List
# from app.config import settings
from app.utils.security import get_current_user
from app.models.user import UserModel


@router.get("/stream/{user_id}/{filename}")
async def stream_video(
    user_id: str = Path(...),
    filename: str = Path(...),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Stream một video đã xử lý
    """
    # Kiểm tra quyền truy cập (tùy chọn - có thể bỏ nếu không cần kiểm tra quyền)
    if str(current_user.id) != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập video này")
    
    # Tạo đường dẫn đến file video
    processed_dir = os.path.join(settings.PROCESSED_DIR, f"user_{user_id}")
    file_path = os.path.join(processed_dir, filename)
    
    # Kiểm tra xem file có tồn tại không
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video không tồn tại")
    
    # Trả về file video để stream
    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=filename
    )

@router.get("/{video_id}/processed")
async def get_processed_video(
    video_id: str = Path(...),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Lấy thông tin về video đã xử lý
    """
    # Tìm thông tin video đã xử lý trong database
    processed_video = await processed_video_collection.find_one({
        "video_id": ObjectId(video_id),
        "status": "completed"
    })
    
    if not processed_video:
        # Kiểm tra xem video có đang xử lý không
        processing_video = await processed_video_collection.find_one({
            "video_id": ObjectId(video_id),
            "status": "processing"
        })
        
        if processing_video:
            raise HTTPException(
                status_code=202, 
                detail="Video đang được xử lý"
            )
        else:
            raise HTTPException(
                status_code=404, 
                detail="Không tìm thấy thông tin video đã xử lý"
            )
    
    # Chuyển đổi ObjectId sang chuỗi để có thể serialize thành JSON
    processed_video["_id"] = str(processed_video["_id"])
    processed_video["video_id"] = str(processed_video["video_id"])
    
    return processed_video

@router.get("/", response_model=List[VideoResponse])
async def get_videos(
    skip: int = 0,
    limit: int = 10,
    current_user = Depends(get_current_active_user)
):
    videos = []
    # Chỉ lấy video của người dùng hiện tại
    cursor = video_collection.find(
        {"user_id": current_user["_id"]}
    ).sort("upload_date", -1).skip(skip).limit(limit)
    
    async for video in cursor:
        videos.append({
            "id": str(video["_id"]),
            "user_id": str(video["user_id"]),
            "title": video["title"],
            "description": video.get("description"),
            "original_filename": video.get("original_filename"),
            "file_path": video.get("file_path"),
            "url": video.get("url"),
            "source_type": video["source_type"],
            "upload_date": video["upload_date"],
            "duration": video.get("duration"),
            "size": video.get("size"),
            "status": video["status"]
        })
    
    return videos

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: str,
    current_user = Depends(get_current_active_user)
):
    # Kiểm tra id hợp lệ
    if not ObjectId.is_valid(video_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video ID"
        )
    
    video = await video_collection.find_one({"_id": ObjectId(video_id)})
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Kiểm tra quyền truy cập
    if str(video["user_id"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return {
        "id": str(video["_id"]),
        "user_id": str(video["user_id"]),
        "title": video["title"],
        "description": video.get("description"),
        "original_filename": video.get("original_filename"),
        "file_path": video.get("file_path"),
        "url": video.get("url"),
        "source_type": video["source_type"],
        "upload_date": video["upload_date"],
        "duration": video.get("duration"),
        "size": video.get("size"),
        "status": video["status"]
    }

@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video_endpoint(
    video_id: str,
    current_user = Depends(get_current_active_user)
):
    # Kiểm tra id hợp lệ
    if not ObjectId.is_valid(video_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video ID"
        )
    
    # Gọi service xóa video
    await delete_video(
        video_id=video_id,
        user_id=str(current_user["_id"]),
        is_admin=(current_user["role"] == "admin")
    )
    
    return None

@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: str,
    video_update: VideoUpdate,
    current_user = Depends(get_current_active_user)
):
    # Kiểm tra id hợp lệ
    if not ObjectId.is_valid(video_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video ID"
        )
    
    # Lấy thông tin video hiện tại
    video = await video_collection.find_one({"_id": ObjectId(video_id)})
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Kiểm tra quyền truy cập
    if str(video["user_id"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Lọc bỏ các trường None
    update_data = {k: v for k, v in video_update.dict().items() if v is not None}
    
    if update_data:
        # Admin mới có quyền thay đổi trạng thái
        if "status" in update_data and current_user["role"] != "admin":
            del update_data["status"]
        
        # Nếu video đang được xử lý hoặc đã hoàn thành, không cho phép thay đổi title & description
        if video["status"] in ["processing", "completed"] and current_user["role"] != "admin":
            if "title" in update_data:
                del update_data["title"]
            if "description" in update_data:
                del update_data["description"]
        
        if update_data:  # Vẫn còn dữ liệu để cập nhật
            result = await video_collection.update_one(
                {"_id": ObjectId(video_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_304_NOT_MODIFIED,
                    detail="Video data not modified"
                )
    
    # Lấy thông tin video sau khi cập nhật
    updated_video = await video_collection.find_one({"_id": ObjectId(video_id)})
    
    return {
        "id": str(updated_video["_id"]),
        "user_id": str(updated_video["user_id"]),
        "title": updated_video["title"],
        "description": updated_video.get("description"),
        "original_filename": updated_video.get("original_filename"),
        "file_path": updated_video.get("file_path"),
        "url": updated_video.get("url"),
        "source_type": updated_video["source_type"],
        "upload_date": updated_video["upload_date"],
        "duration": updated_video.get("duration"),
        "size": updated_video.get("size"),
        "status": updated_video["status"]
    }

@router.get("/{video_id}/processed", response_model=ProcessedVideoResponse)
async def get_processed_video(
    video_id: str,
    current_user = Depends(get_current_active_user)
):
    # Kiểm tra id hợp lệ
    if not ObjectId.is_valid(video_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video ID"
        )
    
    # Lấy thông tin video gốc để kiểm tra quyền truy cập
    original_video = await video_collection.find_one({"_id": ObjectId(video_id)})
    
    if not original_video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Kiểm tra quyền truy cập
    if str(original_video["user_id"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Lấy thông tin video đã xử lý
    processed_video = await processed_video_collection.find_one({"video_id": ObjectId(video_id)})
    
    if not processed_video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processed video not found"
        )
    
    return {
        "id": str(processed_video["_id"]),
        "video_id": str(processed_video["video_id"]),
        "file_path": processed_video.get("file_path"),
        "output_url": processed_video.get("output_url"),
        "created_at": processed_video["created_at"],
        "processing_start_time": processed_video.get("processing_start_time"),
        "processing_end_time": processed_video.get("processing_end_time"),
        "status": processed_video["status"],
        "error_message": processed_video.get("error_message"),
        "size": processed_video.get("size"),
        "duration": processed_video.get("duration"),
        "metadata": processed_video.get("metadata")
    }

@router.get("/user/{user_id}", response_model=List[VideoResponse])
async def get_user_videos(
    user_id: str = Path(...),
    skip: int = Query(0),
    limit: int = Query(10),
    current_user = Depends(get_current_active_user)
):
    # Kiểm tra id hợp lệ
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    # Chỉ admin hoặc chính người dùng mới có thể xem video của họ
    if str(current_user["_id"]) != user_id and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    videos = []
    cursor = video_collection.find(
        {"user_id": ObjectId(user_id)}
    ).sort("upload_date", -1).skip(skip).limit(limit)
    
    async for video in cursor:
        videos.append({
            "id": str(video["_id"]),
            "user_id": str(video["user_id"]),
            "title": video["title"],
            "description": video.get("description"),
            "original_filename": video.get("original_filename"),
            "file_path": video.get("file_path"),
            "url": video.get("url"),
            "source_type": video["source_type"],
            "upload_date": video["upload_date"],
            "duration": video.get("duration"),
            "size": video.get("size"),
            "status": video["status"]
        })
    
    return videos

@router.get("/status/{status}", response_model=List[VideoResponse])
async def get_videos_by_status(
    status: str = Path(...),
    skip: int = Query(0),
    limit: int = Query(10),
    current_user = Depends(get_current_active_user)
):
    # Kiểm tra trạng thái hợp lệ
    valid_statuses = ["pending", "processing", "completed", "failed"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Allowed values: {', '.join(valid_statuses)}"
        )
    
    # Xác định điều kiện tìm kiếm
    query = {"status": status}
    
    # Nếu không phải admin, chỉ lấy video của người dùng hiện tại
    if current_user["role"] != "admin":
        query["user_id"] = current_user["_id"]
    
    videos = []
    cursor = video_collection.find(query).sort("upload_date", -1).skip(skip).limit(limit)
    
    async for video in cursor:
        videos.append({
            "id": str(video["_id"]),
            "user_id": str(video["user_id"]),
            "title": video["title"],
            "description": video.get("description"),
            "original_filename": video.get("original_filename"),
            "file_path": video.get("file_path"),
            "url": video.get("url"),
            "source_type": video["source_type"],
            "upload_date": video["upload_date"],
            "duration": video.get("duration"),
            "size": video.get("size"),
            "status": video["status"]
        })
    
    return videos

@router.put("/{video_id}/retry", response_model=VideoResponse)
async def retry_processing(
    background_tasks: BackgroundTasks,
    video_id: str,
    current_user = Depends(get_current_active_user)
):
    # Kiểm tra id hợp lệ
    if not ObjectId.is_valid(video_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video ID"
        )
    
    # Lấy thông tin video hiện tại
    video = await video_collection.find_one({"_id": ObjectId(video_id)})
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Kiểm tra quyền truy cập
    if str(video["user_id"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Chỉ có thể thử lại nếu trạng thái là 'failed'
    if video["status"] != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed videos"
        )
    
    # Cập nhật trạng thái video sang 'pending'
    await video_collection.update_one(
        {"_id": ObjectId(video_id)},
        {"$set": {"status": "pending"}}
    )
    
    # Xóa bản ghi processed video cũ nếu có
    await processed_video_collection.delete_many({"video_id": ObjectId(video_id)})
    
    # Thêm task xử lý video vào background
    background_tasks.add_task(process_video, video_id)
    
    # Lấy thông tin video sau khi cập nhật
    updated_video = await video_collection.find_one({"_id": ObjectId(video_id)})
    
    return {
        "id": str(updated_video["_id"]),
        "user_id": str(updated_video["user_id"]),
        "title": updated_video["title"],
        "description": updated_video.get("description"),
        "original_filename": updated_video.get("original_filename"),
        "file_path": updated_video.get("file_path"),
        "url": updated_video.get("url"),
        "source_type": updated_video["source_type"],
        "upload_date": updated_video["upload_date"],
        "duration": updated_video.get("duration"),
        "size": updated_video.get("size"),
        "status": updated_video["status"]
    }

@router.get("/search/", response_model=List[VideoResponse])
async def search_videos(
    query: str = Query(..., min_length=1),
    skip: int = Query(0),
    limit: int = Query(10),
    current_user = Depends(get_current_active_user)
):
    # Tìm kiếm dựa trên title hoặc description
    search_query = {
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}}
        ]
    }
    
    # Nếu không phải admin, chỉ tìm kiếm video của người dùng hiện tại
    if current_user["role"] != "admin":
        search_query["user_id"] = current_user["_id"]
    
    videos = []
    cursor = video_collection.find(search_query).sort("upload_date", -1).skip(skip).limit(limit)
    
    async for video in cursor:
        videos.append({
            "id": str(video["_id"]),
            "user_id": str(video["user_id"]),
            "title": video["title"],
            "description": video.get("description"),
            "original_filename": video.get("original_filename"),
            "file_path": video.get("file_path"),
            "url": video.get("url"),
            "source_type": video["source_type"],
            "upload_date": video["upload_date"],
            "duration": video.get("duration"),
            "size": video.get("size"),
            "status": video["status"]
        })
    
    return videos

from app.services.video_service import track_video_service
# Định nghĩa API route track_video
@router.get("/track_video/{video_id}")
async def track_video(video_id: str):
    try:
        result = await track_video_service(video_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")
# @router.get("time_detection/{video_id}")
# async def time_detection(video_id: str):
#     try  :
#         result = await get_detection()
#         return result
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(status_code=500 , detail=f"lỗi:{str(e)}")

@router.get("/serve/{path:path}")
async def serve_video(path: str):
    full_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, path))  # ✅ CHUẨN
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=full_path, media_type="video/mp4", filename=os.path.basename(full_path))
@router.get("/videos/{video_id}")
async def get_video(video_id: str):
    video = await video_collection.find_one({"_id": ObjectId(video_id)})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return {
        "video": {
            "id": str(video["_id"]),
            "title": video.get("title"),
            "description": video.get("description"),
            "video_url": video.get("video_url") or video.get("file_path") or "",
            "status": video.get("status")
        }
    }
