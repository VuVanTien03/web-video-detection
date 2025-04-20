# File: app/routes/user.py
from fastapi import APIRouter, Body, Depends, HTTPException, status
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserInDB
from app.utils.security import get_password_hash, get_current_active_user
from app.database import user_collection
from datetime import datetime
from bson import ObjectId
from typing import List

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate = Body(...)):
    # Check if username already exists
    if await user_collection.find_one({"username": user.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if await user_collection.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = {
        "username": user.username,
        "email": user.email,
        "password_hash": hashed_password,
        "full_name": user.full_name,
        "created_at": datetime.now(),
        "role": "user",
        "status": "active"
    }
    
    result = await user_collection.insert_one(new_user)
    
    created_user = await user_collection.find_one({"_id": result.inserted_id})
    
    return {
        "id": str(created_user["_id"]),
        "username": created_user["username"],
        "email": created_user["email"],
        "full_name": created_user.get("full_name"),
        "role": created_user["role"],
        "status": created_user["status"]
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_active_user)):
    return {
        "id": str(current_user["_id"]),
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "role": current_user["role"],
        "status": current_user["status"]
    }

@router.put("/me", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    current_user = Depends(get_current_active_user)
):
    # Lọc bỏ các trường None
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    
    if update_data:
        update_data["updated_at"] = datetime.now()
        
        # Không cho phép người dùng thông thường thay đổi role
        if "role" in update_data and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        result = await user_collection.update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_304_NOT_MODIFIED,
                detail="User data not modified"
            )
    
    updated_user = await user_collection.find_one({"_id": current_user["_id"]})
    
    return {
        "id": str(updated_user["_id"]),
        "username": updated_user["username"],
        "email": updated_user["email"],
        "full_name": updated_user.get("full_name"),
        "role": updated_user["role"],
        "status": updated_user["status"]
    }

@router.get("/", response_model=List[UserResponse])
async def read_users(skip: int = 0, limit: int = 100, current_user = Depends(get_current_active_user)):
    # Chỉ admin mới có thể xem danh sách người dùng
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = []
    cursor = user_collection.find().skip(skip).limit(limit)
    
    async for user in cursor:
        users.append({
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "role": user["role"],
            "status": user["status"]
        })
    
    return users