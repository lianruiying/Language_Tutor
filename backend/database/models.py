from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.database.database import Base, engine

# 创建所有表
Base.metadata.create_all(bind=engine)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 可以添加其他用户相关字段，如：
    # full_name = Column(String, index=True)
    # language_preference = Column(String)
