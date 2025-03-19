from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from backend.database.models import User
from backend.database.schemas import UserCreate, UserUpdate, UserInDB
from backend.crud import users
from backend.api.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=UserInDB)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    创建新用户
    """
    # 检查用户名是否已存在
    user = users.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="该用户名已被使用"
        )
    
    # 检查邮箱是否已存在
    user = users.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="该邮箱已被注册"
        )
    
    try:
        # 创建用户
        user = users.create(db, obj_in=user_in)
        
        # 确保返回的是一个符合UserInDB模型的字典
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        
        return user_data
    except Exception as e:
        # 记录错误并返回友好的错误信息
        print(f"创建用户时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="创建用户时发生错误，请稍后再试"
        )