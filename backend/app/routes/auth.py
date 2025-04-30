from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from app.utils.security import authenticate_user, create_access_token, get_password_hash
from app.config import settings
from app.routes.user import user_collection  # Lấy user_collection từ user.py
from app.schemas.user import UserCreate, UserResponse
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["authentication"])

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},  # <<< Đây, cần nhét email vào 'sub'
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Route đăng ký người dùng mới (signup)
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    # Kiểm tra tên người dùng đã tồn tại chưa
    if await user_collection.find_one({"username": user.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Kiểm tra email đã tồn tại chưa
    if await user_collection.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Tạo người dùng mới
    hashed_password = get_password_hash(user.password)
    new_user = {
        "username": user.username,
        "email": user.email,
        "password_hash": hashed_password,
        "raw_password": user.password,
        "full_name": user.full_name,
        "created_at": datetime.now(),
        "role": "user",
        "status": "active"
    }
    
    # Lưu người dùng vào cơ sở dữ liệu
    result = await user_collection.insert_one(new_user)
    
    # Trả về thông tin người dùng mới
    created_user = await user_collection.find_one({"_id": result.inserted_id})
    
    return {
        "id": str(created_user["_id"]),
        "username": created_user["username"],
        "email": created_user["email"],
        "full_name": created_user.get("full_name"),
        "role": created_user["role"],
        "status": created_user["status"]
    }
