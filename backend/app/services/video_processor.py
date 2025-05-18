import os
import time
import subprocess
import asyncio
from datetime import datetime
from bson import ObjectId
from app.database import video_collection, processed_video_collection
from app.config import settings
import json
import yt_dlp
from pymongo import UpdateOne
import shutil


async def process_video(video_id: str):
    """
    Xử lý video trong background
    """
    processed_video_id = None
    try:
        # Cập nhật trạng thái video sang 'processing'
        await video_collection.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": {"status": "processing"}}
        )
        
        # Lấy thông tin video
        video = await video_collection.find_one({"_id": ObjectId(video_id)})
        if not video:
            raise Exception(f"Video with ID {video_id} not found")
        
        # Tạo bản ghi cho video đã xử lý
        processing_record = {
            "video_id": ObjectId(video_id),
            "created_at": datetime.now(),
            "processing_start_time": datetime.now(),
            "status": "processing"
        }
        
        result = await processed_video_collection.insert_one(processing_record)
        processed_video_id = result.inserted_id
        
        # Tạo thư mục cho video đã xử lý
        user_id = str(video["user_id"])
        processed_dir = os.path.join(settings.PROCESSED_DIR, f"user_{user_id}")
        os.makedirs(processed_dir, exist_ok=True)
        
        output_filename = f"processed_{video_id}.mp4"
        output_path = os.path.join(processed_dir, output_filename)
        
        # Xử lý video dựa trên loại nguồn
        if video.get("source_type") == "local":
            input_path = video["file_path"]
            # Xử lý video đã tải lên
            video_info = await get_video_info(input_path)
            await process_local_video(input_path, output_path)
        elif video.get("source_type") == "url" and video.get("url"):
            url = video["url"]
            # Tải và cập nhật tiêu đề video từ YouTube (nếu là link YouTube)
            if "youtube.com" in url or "youtu.be" in url:
                video_info = await download_youtube_video(url, processed_dir, video_id)
                
                # Cập nhật tiêu đề vào MongoDB nếu title không được đặt
                if video_info.get("title") and not video.get("title"):
                    await video_collection.update_one(
                        {"_id": ObjectId(video_id)},
                        {"$set": {"title": video_info.get("title")}}
                    )
                
                # Đường dẫn tới file tạm
                temp_path = os.path.join(processed_dir, f"temp_{video_id}.mp4")
                
                # Xử lý video tải về
                await process_local_video(temp_path, output_path)
                
                # Xóa file tạm
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            else:
                # Xử lý URL không phải YouTube
                temp_path = os.path.join(processed_dir, f"temp_{video_id}.mp4")
                await download_generic_video(url, temp_path)
                video_info = await get_video_info(temp_path)
                await process_local_video(temp_path, output_path)
                
                # Xóa file tạm
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            raise Exception("Neither file_path nor URL provided for video processing")
        
        # Lấy thông tin video đã xử lý
        processed_video_info = await get_video_info(output_path)
        output_size = os.path.getsize(output_path)
        
        # Tạo URL truy cập
        output_url = f"/api/v1/videos/stream/{user_id}/{output_filename}"
        
        # Cập nhật thông tin video đã xử lý
        await processed_video_collection.update_one(
            {"_id": processed_video_id},
            {"$set": {
                "file_path": output_path,
                "output_url": output_url,
                "processing_end_time": datetime.now(),
                "status": "completed",
                "size": output_size,
                "duration": processed_video_info.get("duration"),
                "metadata": processed_video_info
            }}
        )
        
        # Cập nhật thông tin video gốc
        await video_collection.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": {
                "status": "completed",
                "duration": video_info.get("duration"),
                "video_url": output_url,  # Thêm URL của video đã xử lý
                "file_path": output_path
            }}
        )
    
    except Exception as e:
        # Xử lý lỗi
        error_message = str(e)
        import traceback
        print(f"[ERROR] Video ID: {video_id}\n{traceback.format_exc()}")

        
        # Cập nhật trạng thái video sang 'failed'
        await video_collection.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": {"status": "failed", "error_message": error_message}}
        )
        
        # Chỉ cập nhật bản ghi processed_video nếu đã được tạo
        if processed_video_id:
            await processed_video_collection.update_one(
                {"_id": processed_video_id},
                {"$set": {
                    "status": "failed",
                    "error_message": error_message,
                    "processing_end_time": datetime.now()
                }}
            )


async def download_youtube_video(url: str, output_dir: str, video_id: str) -> dict:
    """
    Tải video từ YouTube sử dụng yt-dlp và trả về thông tin video
    """
    output_path = os.path.join(output_dir, f"temp_{video_id}.mp4")
    
    try:
        # Cấu hình options cho yt-dlp
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Ưu tiên định dạng mp4
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
        }
        
        # Tải video và lấy thông tin
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            
        # Trả về thông tin video
        video_info = {
            "title": info_dict.get('title', 'Unknown Title'),
            "duration": info_dict.get('duration', 0),
            "width": info_dict.get('width'),
            "height": info_dict.get('height'),
            "format": info_dict.get('format', 'unknown'),
            "extractor": info_dict.get('extractor', 'youtube'),
            "size": os.path.getsize(output_path) if os.path.exists(output_path) else 0
        }
        
        return video_info
            
    except Exception as e:
        raise Exception(f"Error downloading from YouTube: {str(e)}")


async def download_generic_video(url: str, output_path: str) -> bool:
    """
    Tải video từ URL không phải YouTube
    """
    try:
        # Sử dụng ffmpeg để tải video
        cmd = [
            "ffmpeg",
            "-i", url,
            "-c", "copy",  # Chỉ copy stream, không encode lại
            "-y",  # Ghi đè nếu file đã tồn tại
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Failed to download video: {stderr.decode()}")
        
        return True
    
    except Exception as e:
        raise Exception(f"Error downloading video: {str(e)}")


async def get_video_info(file_path: str) -> dict:
    """
    Lấy thông tin của video bằng ffprobe
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Failed to get video info: {stderr.decode()}")
        
        info = json.loads(stdout.decode())
        
        # Trích xuất thông tin quan trọng
        video_info = {}
        
        if "format" in info:
            format_info = info["format"]
            video_info["format"] = format_info.get("format_name")
            video_info["duration"] = int(float(format_info.get("duration", 0)))
            video_info["size"] = int(format_info.get("size", 0))
            video_info["bit_rate"] = int(format_info.get("bit_rate", 0))
        
        # Lấy thông tin về video stream
        video_stream = None
        audio_stream = None
        
        if "streams" in info:
            for stream in info["streams"]:
                if stream.get("codec_type") == "video" and not video_stream:
                    video_stream = stream
                elif stream.get("codec_type") == "audio" and not audio_stream:
                    audio_stream = stream
        
        if video_stream:
            video_info["width"] = video_stream.get("width")
            video_info["height"] = video_stream.get("height")
            video_info["codec"] = video_stream.get("codec_name")
            try:
                video_info["fps"] = eval(video_stream.get("r_frame_rate", "0/1")) if video_stream.get("r_frame_rate") else 0
            except:
                video_info["fps"] = 0
        
        if audio_stream:
            video_info["audio_codec"] = audio_stream.get("codec_name")
            video_info["audio_channels"] = audio_stream.get("channels")
            video_info["audio_sample_rate"] = audio_stream.get("sample_rate")
        
        return video_info
    
    except Exception as e:
        # Nếu có lỗi, trả về thông tin tối thiểu
        print(f"Error getting video info: {str(e)}")
        return {
            "error": str(e),
            "duration": 0
        }


async def process_local_video(input_path: str, output_path: str) -> bool:
    """
    Xử lý video sử dụng ffmpeg
    """
    try:
        if not os.path.exists(input_path):
            raise Exception(f"Input file not found: {input_path}")
        
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-y",
            output_path
        ]
        
        def run_ffmpeg():
            return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        result = await asyncio.to_thread(run_ffmpeg)

        if result.returncode != 0:
            raise Exception(f"Failed to process video: {result.stderr.decode()}")
        
        return True
    
    except Exception as e:
        raise Exception(f"Error processing video: {str(e)}")
