# File: app/utils/validators.py
import os
import re
from fastapi import HTTPException, status
from app.config import settings

def validate_video_file_extension(filename: str) -> bool:
    """
    Kiểm tra phần mở rộng của file video
    """
    if not filename:
        return False
    
    file_extension = os.path.splitext(filename)[1].lower().replace(".", "")
    return file_extension in settings.ALLOWED_VIDEO_TYPES

def validate_video_size(file_size: int) -> bool:
    """
    Kiểm tra kích thước của file video
    """
    return file_size <= settings.MAX_VIDEO_SIZE

def validate_url(url: str) -> bool:
    """
    Kiểm tra URL có hợp lệ không
    """
    # Kiểm tra URL cơ bản
    url_pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))

def validate_username(username: str) -> bool:
    """
    Kiểm tra username có hợp lệ không
    """
    # Username chỉ chứa chữ cái, số, dấu gạch dưới và gạch ngang
    username_pattern = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')
    return bool(username_pattern.match(username))

def validate_email(email: str) -> bool:
    """
    Kiểm tra email có hợp lệ không
    """
    # Kiểm tra email cơ bản
    email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    return bool(email_pattern.match(email))

def validate_password(password: str) -> bool:
    """
    Kiểm tra password có đủ mạnh không
    """
    # Password có ít nhất 8 ký tự, bao gồm chữ cái, số
    if len(password) < 8:
        return False
    
    has_letter = re.search(r'[a-zA-Z]', password)
    has_number = re.search(r'\d', password)
    
    return bool(has_letter and has_number)