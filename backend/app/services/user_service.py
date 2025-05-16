# File: app/services/user_service.py
from app.database import user_collection
from app.utils.security import get_password_hash
from bson import ObjectId
from fastapi import HTTPException, status
from datetime import datetime

async def create_user(user_data):
    """
    Tạo người dùng mới
    """
    # Kiểm tra username đã tồn tại chưa
    if await user_collection.find_one({"username": user_data.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Kiểm tra email đã tồn tại chưa
    if await user_collection.find_one({"email": user_data.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Tạo user mới
    new_user = {
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": hashed_password,
        "full_name": user_data.full_name,
        "created_at": datetime.now(),
        "role": "user",
        "status": "active"
    }
    
    result = await user_collection.insert_one(new_user)
    
    # Lấy thông tin user vừa tạo
    created_user = await user_collection.find_one({"_id": result.inserted_id})
    
    return created_user

async def get_user_by_id(user_id):
    """
    Lấy thông tin người dùng theo id
    """
    if not ObjectId.is_valid(user_id):
        return None
    
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    return user

async def get_user_by_username(username):
    """
    Lấy thông tin người dùng theo username
    """
    user = await user_collection.find_one({"username": username})
    return user

async def update_user(user_id, update_data):
    """
    Cập nhật thông tin người dùng
    """
    # Lọc bỏ các trường None
    filtered_data = {k: v for k, v in update_data.items() if v is not None}
    
    if filtered_data:
        filtered_data["updated_at"] = datetime.now()
        
        result = await user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": filtered_data}
        )
        
        if result.modified_count == 0:
            return None
    
    # Lấy thông tin user sau khi cập nhật
    updated_user = await user_collection.find_one({"_id": ObjectId(user_id)})
    return updated_user