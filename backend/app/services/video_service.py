# File: app/services/video_service.py
import traceback
from collections import deque

from app.database import video_collection, processed_video_collection, user_collection
from bson import ObjectId
from datetime import datetime
import os
from fastapi import HTTPException, status, Depends, BackgroundTasks
from app.utils.security import get_current_active_user
from app.config import settings
import cv2
import app.utils.setup_path_yolo
from models.common import DetectMultiBackend, AutoShape
from fastapi import BackgroundTasks, HTTPException, Depends
from fastapi.responses import StreamingResponse
import torch
import queue
import threading
import numpy as np
import time
import json
from pathlib import Path

async def get_video_by_id(video_id):
    """
    Lấy thông tin video theo id
    """
    if not ObjectId.is_valid(video_id):
        return None
    
    video = await video_collection.find_one({"_id": ObjectId(video_id)})
    return video

async def get_processed_video_by_video_id(video_id):
    """
    Lấy thông tin video đã xử lý theo id video gốc
    """
    if not ObjectId.is_valid(video_id):
        return None
    
    processed_video = await processed_video_collection.find_one({"video_id": ObjectId(video_id)})
    return processed_video

async def get_user_videos(user_id, skip=0, limit=10):
    """
    Lấy danh sách video của người dùng
    """
    videos = []
    cursor = video_collection.find(
        {"user_id": ObjectId(user_id)}
    ).sort("upload_date", -1).skip(skip).limit(limit)
    
    async for video in cursor:
        videos.append(video)
    
    return videos

async def get_all_videos(user_id):
    """
    get all videos of user 
    """
    videos = []
    cursor = video_collection.find(
        {"user_id": ObjectId(user_id)}
    )
    
    async for video in cursor:
        videos.append(video)
    return videos 

async def delete_video(video_id, user_id, is_admin=False):
    """
    Xóa video
    """
    if not ObjectId.is_valid(video_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video ID"
        )
    
    # Lấy thông tin video
    video = await video_collection.find_one({"_id": ObjectId(video_id)})
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Kiểm tra quyền
    if str(video["user_id"]) != str(user_id) and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Xóa file video gốc nếu có
    if video.get("file_path") and os.path.exists(video["file_path"]):
        os.remove(video["file_path"])
    
    # Lấy thông tin video đã xử lý
    processed_video = await processed_video_collection.find_one({"video_id": ObjectId(video_id)})
    
    # Xóa file video đã xử lý nếu có
    if processed_video and processed_video.get("file_path") and os.path.exists(processed_video["file_path"]):
        os.remove(processed_video["file_path"])
    
    # Xóa thông tin video đã xử lý trong database
    if processed_video:
        await processed_video_collection.delete_one({"_id": processed_video["_id"]})
    
    # Xóa thông tin video gốc trong database
    await video_collection.delete_one({"_id": ObjectId(video_id)})
    
    return True

async def get_path_video(video_id, user=Depends(get_current_active_user)):
    """
    Lấy đường dẫn file video
    """
    if not ObjectId.is_valid(video_id):
        raise HTTPException(status_code=400, detail="Invalid video ID")
    
    object_id = ObjectId(video_id)
    user_id = user["_id"]
    
    # Lấy thông tin video
    video = await video_collection.find_one({"_id": object_id, "user_id": ObjectId(user_id)})
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video['file_path']
import asyncio
# Đường dẫn tuyệt đối từ thư mục gốc của project
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_WEIGHTS_PATH = BASE_DIR / "services" / "gelan_t.pt"


class FrameBuffer:
    _buffer  = None # singlenton instance
    _lock = threading.Lock()

    def __init__(self , max_size = 5):
        self.input_frames = deque(maxlen=max_size)
        self.processed_frames = queue.Queue(maxsize=max_size)
        self.detection_list = []
        self.processing = True
        self.lock = threading.Lock()
        self.worker_thread = None
        self.reset_called = False
    @classmethod
    def get_buffer(cls , max_size = 5 , force_new = False):
        """
        get singleton buffer instance or create new if needed
        args :
         maxsize : max size of frame buffer
         force_new = : if true , always create new instance
        """
        with cls._lock:
            if cls._buffer is None or force_new:
                cls._buffer = FrameBuffer(max_size = max_size)
            return cls._buffer
    @classmethod
    def reset_singleton(cls):
        """force reset the singleton instance completely"""
        with cls._lock:
            if cls._buffer is not None:
                cls._buffer.stop()
                cls._buffer = None

    def put_input(self , frame):
        """ add a new frame to the input queue"""
        if self.processing and not self.reset_called:
            self.input_frames.append(frame)
    def get_input(self):
        """get the nex frame to process (lifo) """
        if not self.processing or self.reset_called:
            return None
        try :
            return self.input_frames.pop()
        except IndexError:
            return None

    def put_processed(self, frame, detection):
        """Store processed frame with its detection results"""
        if not self.processing or self.reset_called:
            return

        with self.lock:
            try:
                self.processed_frames.put_nowait((frame, detection))
            except queue.Full:
                # If queue is full, remove oldest item and add new one
                try:
                    self.processed_frames.get_nowait()
                    self.processed_frames.put_nowait((frame, detection))
                except (queue.Empty, queue.Full):
                    pass

    def get_processed_frame(self):
        """Get the next processed frame from queue"""
        if not self.processing or self.reset_called:
            raise queue.Empty()

        with self.lock:
            return self.processed_frames.get_nowait()

    def put_detections(self, detection_data):
        """Store detection results for API access"""
        if not self.processing or self.reset_called:
            return

        with self.lock:
            self.detection_list.append(detection_data)
            # Keep list at reasonable size
            if len(self.detection_list) > 100:
                self.detection_list = self.detection_list[-100:]

    def get_violence_detection(self):
        with self.lock:
            return self.detection_list.copy()
    def get_detections(self):
        """Get all stored detection results"""
        with self.lock:
            return self.detection_list.copy()

    def stop(self):
        """Stop processing and release resources"""
        self.processing = False
        self.reset_called = True

        # Clear all queues to release memory
        with self.lock:
            self.input_frames.clear()
            while not self.processed_frames.empty():
                try:
                    self.processed_frames.get_nowait()
                except queue.Empty:
                    break

    def format_time(self, seconds):
        """Định dạng thời gian từ giây thành chuỗi MM:SS"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    def hard_reset(self):
        """Complete reset of buffer state for reuse"""
        self.stop()  # First stop all processing

        with self.lock:
            # Reset all data structures
            self.input_frames.clear()

            # Empty the queue
            while not self.processed_frames.empty():
                try:
                    self.processed_frames.get_nowait()
                except queue.Empty:
                    break

            # Reset detection list and state flags
            self.detection_list = []
            self.processing = True
            self.reset_called = False

            # Signal completion
            print("FrameBuffer hard reset completed")


# YOLO worker function with improved error handling and state management
def yolo_worker(model, frame_buffer, conf_threshold=0.5):
    """Process frames using YOLO model in a separate thread"""
    worker_id = threading.get_ident()
    print(f"YOLO worker started with ID: {worker_id}")

    error_count = 0
    max_errors = 5  # Max consecutive errors before backing off

    try:
        while frame_buffer.processing and not frame_buffer.reset_called:
            try:
                frame = frame_buffer.get_input()
                if frame is None:
                    time.sleep(0.01)  # Sleep to avoid CPU spinning
                    continue

                with torch.no_grad():
                    # Run YOLO predictions on the frame
                    predictions = model(frame)
                    frame_buffer.put_processed(frame, predictions)

                # Reset error count on successful processing
                error_count = 0

            except Exception as e:
                error_count += 1
                print(f"Error in YOLO worker ({worker_id}): {str(e)}")

                # Exponential backoff on repeated errors
                sleep_time = min(0.1 * (2 ** error_count), 5.0)
                time.sleep(sleep_time)

                # Break loop if too many consecutive errors
                if error_count >= max_errors:
                    print(f"Too many errors in YOLO worker, stopping: {worker_id}")
                    break

    except Exception as e:
        print(f"Critical error in YOLO worker thread ({worker_id}): {str(e)}")

    finally:
        print(f"YOLO worker thread exiting: {worker_id}")


# Improved video streaming function with better resource management
def show_video_stream(video_path, model, device="cpu", conf_threshold=0.8):
    """Process video and return a streaming response with detections"""
    # Reset and get a clean FrameBuffer instance
    FrameBuffer.reset_singleton()
    frame_buffer = FrameBuffer.get_buffer(max_size=10)

    try:
        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_time = 1.0 / fps if fps > 0 else 0.03
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Start worker thread - ensure it's only started once
        worker_thread = threading.Thread(
            target=yolo_worker,
            args=(model, frame_buffer, conf_threshold),
            daemon=True
        )

        # Store the thread in the buffer for monitoring
        frame_buffer.worker_thread = worker_thread
        worker_thread.start()
        print(f"Started YOLO worker thread: {worker_thread.ident}")

        def generate():
            """Generator for video frames with detection overlays"""
            frame_count = 0
            last_time = time.time()
            detection_batch = []
            batch_counter = 0
            stream_start_time = time.time()
            last_violence_count = 0

            try:
                print("Starting video stream processing")
                while cap.isOpened() and frame_buffer.processing:
                    ret, frame = cap.read()
                    if not ret:
                        print("End of video reached")
                        break

                    frame_count += 1
                    current_time = time.time()
                    elapsed = current_time - last_time

                    # Calculate current video timestamp
                    current_video_time = frame_count / fps if fps > 0 else 0
                    progress_percent = (frame_count / total_frames * 100) if total_frames > 0 else 0

                    # Debug output every 100 frames
                    if frame_count % 100 == 0:
                        print(f"Processing frame {frame_count}/{total_frames} ({progress_percent:.1f}%)")

                    # Queue frame for processing
                    frame_copy = frame.copy()  # Explicit copy to avoid reference issues
                    frame_buffer.put_input(frame_copy)

                    # Try to get processed results
                    detections = []
                    try:
                        result = frame_buffer.get_processed_frame()
                        processed_frame, predictions = result

                        # Record detection timestamp
                        timestamp = current_video_time

                        # Process YOLO predictions
                        if len(predictions.pred) > 0 and len(predictions.pred[0]) > 0:
                            for det in predictions.pred[0]:
                                x1, y1, x2, y2, conf, class_id = det[:6]
                                if conf < 0.85:
                                    continue

                                # Create detection object with explicit Python types
                                detection = {
                                    "time": round(float(current_video_time), 2),
                                    "frame": int(frame_count),
                                    "confidence": float(conf),
                                    "bounding_box": [float(x1), float(y1), float(x2), float(y2)],
                                    "label": "violence"
                                }
                                detections.append(detection)

                                # Log detections
                                if frame_count % 100 == 0:
                                    print(f"Detection at frame {frame_count}: conf={float(conf):.2f}")

                                # Draw detection on frame
                                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                cv2.putText(frame, f"Violence: {float(conf):.2f}", (x1, y1 - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                            # Store detections for API access
                            if detections:
                                frame_buffer.put_detections((detections, timestamp))
                                detection_batch.extend(detections)
                                last_violence_count = len(detections)
                        # timestamp_text = f"Thời gian: {frame_buffer.format_time(current_video_time)}"
                        # cv2.putText(frame, timestamp_text, (10, 60),
                        #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        #
                        # # Đếm số lượng phát hiện bạo lực trong frame hiện tại
                        # violence_count = len(detections)
                        # cv2.putText(frame, f"violen: {violence_count}", (10, 120),
                        #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                    except queue.Empty:
                        # No processed frame available yet
                        pass
                    timestamp_text = f"time: {frame_buffer.format_time(current_video_time)}"
                    cv2.putText(frame, timestamp_text, (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    violence_count = len(frame_buffer.get_violence_detection())
                    cv2.putText(frame, f"violence: {violence_count}", (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                    ret, buffer = cv2.imencode('.jpg', frame, encode_param)
                    frame_bytes = buffer.tobytes()

                    # Yield frame to client
                    yield (
                            b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' +
                            frame_bytes +
                            b'\r\n'
                    )

                    # Control frame rate
                    processing_time = time.time() - current_time
                    sleep_time = max(0, frame_time - processing_time)
                    if sleep_time > 0:
                        time.sleep(sleep_time)

            except Exception as e:
                print(f"Error in stream generator: {str(e)}")
                # On error, also yield the error to client for visibility
                error_json = json.dumps({"error": str(e)})
                yield (
                        b'--frame\r\n'
                        b'Content-Type: application/json\r\n\r\n' +
                        error_json.encode() + b'\r\n'
                )

            finally:
                # Clean up resources
                print("Cleaning up resources in generator")
                try:
                    if cap.isOpened():
                        cap.release()
                except Exception as e:
                    print(f"Error releasing video capture: {str(e)}")

                # Signal processing completion
                frame_buffer.processing = False
                print("Video stream ended, resources released")

        return StreamingResponse(
            generate(),
            media_type='multipart/x-mixed-replace; boundary=frame'
        )

    except Exception as e:
        # Clean up on error
        try:
            frame_buffer.stop()
            if 'cap' in locals() and cap.isOpened():
                cap.release()
        except:
            pass

        print(f"Error in show_video_stream: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")


# Improved detection stream function
async def get_detection_stream():
    """Generate stream of detection results for API access"""
    frame_buffer = FrameBuffer.get_buffer()

    async def detection_stream():
        last_index = 0
        error_count = 0

        try:
            while frame_buffer.processing and error_count < 5:
                try:
                    detections = frame_buffer.get_detections()

                    # Get new detections since last check
                    if len(detections) > last_index:
                        new_detections = detections[last_index:]
                        last_index = len(detections)

                        # Format and yield detection data
                        detection_data = []
                        for det_group, timestamp in new_detections:
                            for det in det_group:
                                det_copy = det.copy()  # Make a copy to avoid modifying original
                                det_copy["timestamp"] = float(timestamp)
                                detection_data.append(det_copy)

                        if detection_data:
                            detection_json = json.dumps({"detections": detection_data})
                            yield (
                                    b'--frame\r\n'
                                    b'Content-Type: application/json\r\n\r\n' +
                                    detection_json.encode() + b'\r\n'
                            )
                            error_count = 0  # Reset error count on successful yield
                except Exception as e:
                    error_count += 1
                    print(f"Error in detection stream: {str(e)}")

                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Critical error in detection stream: {str(e)}")
            # Notify client of error
            error_json = json.dumps({"error": str(e)})
            yield (
                    b'--frame\r\n'
                    b'Content-Type: application/json\r\n\r\n' +
                    error_json.encode() + b'\r\n'
            )

        finally:
            print("Detection stream ended")

    return StreamingResponse(
        detection_stream(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )


# Service function to process video
async def track_video_service(video_id,weights_path=DEFAULT_WEIGHTS_PATH, device=None):

    """Main service function to process a video with violence detection"""
    # Determine appropriate device
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"Starting video processing service for video_id: {video_id} on device: {device}")

    # Force reset the singleton to ensure clean state
    FrameBuffer.reset_singleton()

    try:
        # Find video in database
        video = await video_collection.find_one({"_id": ObjectId(video_id)})
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        video_path = video["file_path"]
        print(f"Found video path: {video_path}")

        # Check if video file exists
        if not Path(video_path).exists():
            raise HTTPException(status_code=404, detail="Video file not found on server")

        # Load YOLO model
        print(f"Loading YOLO model from: {weights_path}")
        try:
            model_backend = DetectMultiBackend(weights=str(weights_path), device=device)
            model = AutoShape(model_backend)
            model.eval()
            print("YOLO model loaded successfully")
        except Exception as e:
            print(f"Failed to load model: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

        # Return video stream with detections
        print("Starting video stream...")
        return show_video_stream(video_path, model, device=device)

    except Exception as e:
        # Ensure frame buffer is stopped in case of error
        print(f"Error in track_video_service: {str(e)}")
        try:
            FrameBuffer.reset_singleton()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

