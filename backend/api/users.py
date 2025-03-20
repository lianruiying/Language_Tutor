from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from backend.database.schemas import (
    User, UserCreate, UserUpdate, 
    UserLanguage, UserStatistics, UserLearningHistory,
    UserProfileResponse, UserProfileUpdate, UserHistoryResponse
)
from backend.crud import users
from backend.api.dependencies import get_db, get_current_active_user
from backend.database.models import User as DBUser, UserLanguage as DBUserLanguage, UserStatistics as DBUserStatistics, UserLanguage as DBUserLanguage

router = APIRouter()

@router.post("/", response_model=User)
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

@router.get("/profile", response_model=UserProfileResponse)
def get_user_profile(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
) -> Any:
    """获取用户资料"""
    try:
        # 获取用户统计数据
        stats = db.query(DBUserStatistics).filter(DBUserStatistics.user_id == current_user.id).first()
        
        # 获取用户语言学习情况
        languages = db.query(DBUserLanguage).filter(DBUserLanguage.user_id == current_user.id).all()
        
        # 构建响应数据
        return {
            "username": current_user.username,
            "email": current_user.email,
            "avatar": current_user.avatar,
            "learningLanguages": [lang.language for lang in languages],
            "level": {lang.language: lang.level for lang in languages},
            "studyTime": stats.study_time if stats else 0,
            "wordsLearned": stats.words_learned if stats else 0,
            "articlesRead": stats.articles_read if stats else 0
        }
    except Exception as e:
        print(f"获取用户资料失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取用户资料失败: {str(e)}"
        )

@router.get("/history", response_model=List[UserHistoryResponse])
def get_user_history(current_user: DBUser = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """获取用户学习历史"""
    history = db.query(UserLearningHistory).filter(
        UserLearningHistory.user_id == current_user.id
    ).order_by(UserLearningHistory.created_at.desc()).limit(10).all()
    
    return history

@router.put("/profile", response_model=UserProfileResponse)
def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: DBUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新用户资料"""
    # 更新基本信息
    for field, value in profile_update.dict(exclude_unset=True).items():
        if field not in ["learningLanguages", "level"]:
            setattr(current_user, field, value)
    
    # 更新学习语言
    if profile_update.learningLanguages:
        # 删除现有语言
        db.query(DBUserLanguage).filter(DBUserLanguage.user_id == current_user.id).delete()
        
        # 添加新语言
        for lang in profile_update.learningLanguages:
            level = profile_update.level.get(lang, "A1") if profile_update.level else "A1"
            new_lang = DBUserLanguage(
                user_id=current_user.id,
                language=lang,
                level=level
            )
            db.add(new_lang)
    
    db.commit()
    db.refresh(current_user)
    
    # 返回更新后的资料
    return get_user_profile(db, current_user)