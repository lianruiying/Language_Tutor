from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from ..database.models import User
from ..database.schemas import UserCreate, UserUpdate
from ..core.security import get_password_hash, verify_password
from pydantic import BaseModel

def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get(db: Session, id: int) -> Optional[User]:
    return db.query(User).filter(User.id == id).first()

def create(db: Session, obj_in: UserCreate) -> User:
    """创建新用户"""
    # 打印调试信息
    print(f"尝试创建用户: {obj_in.username}, {obj_in.email}")
    
    # 创建哈希密码
    hashed_password = get_password_hash(obj_in.password)
    
    # 创建用户对象
    db_obj = User(
        username=obj_in.username,
        email=obj_in.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False
    )
    
    try:
        # 添加到数据库
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        print(f"用户创建成功: {db_obj.id}")
        return db_obj
    except Exception as e:
        db.rollback()
        print(f"用户创建失败: {str(e)}")
        raise e

def update(db: Session, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]) -> User:
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)
    
    if update_data.get("password"):
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
    
    for field in update_data:
        if hasattr(db_obj, field):
            setattr(db_obj, field, update_data[field])
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def authenticate(db: Session, *, username: str, password: str) -> Optional[User]:
    """验证用户凭据"""
    try:
        # 打印调试信息
        print(f"尝试验证用户: {username}")
        
        # 获取用户
        user = get_by_username(db, username=username)
        if not user:
            print(f"用户不存在: {username}")
            return None
        
        # 验证密码
        if not verify_password(password, user.hashed_password):
            print(f"密码验证失败: {username}")
            return None
        
        print(f"用户验证成功: {username}")
        return user
    except Exception as e:
        print(f"用户验证异常: {str(e)}")
        return None

def is_active(user: User) -> bool:
    return user.is_active

def is_superuser(user: User) -> bool:
    return user.is_superuser

class UserBase(BaseModel):
    class Config:
        from_attributes = True 