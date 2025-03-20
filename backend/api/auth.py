from datetime import timedelta
from typing import Any
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.schemas import Token, User
from backend.crud import users
from backend.core.config import settings
from backend.core.security import create_access_token

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_access_token(
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 兼容的token登录，获取访问令牌
    """
    try:
        print(f"登录请求: username={form_data.username}, password长度={len(form_data.password) if form_data.password else 0}")
        
        user = users.authenticate(db, username=form_data.username, password=form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif not users.is_active(user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="用户未激活"
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return {
            "access_token": create_access_token(user.id, expires_delta=access_token_expires),
            "token_type": "bearer",
        }
    except Exception as e:
        print(f"登录处理错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"登录失败: {str(e)}"
        ) 