from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Float, JSON, Table
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import ARRAY

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
    avatar = Column(String, nullable=True)
    
    # 关系
    user_profile = relationship("UserProfile", back_populates="user", uselist=False)
    languages = relationship("UserLanguage", back_populates="user")
    statistics = relationship("UserStatistics", back_populates="user", uselist=False)
    learning_history = relationship("UserLearningHistory", back_populates="user")
    vocabulary = relationship("UserVocabulary", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    total_study_time = Column(Float, default=0.0)  # 总学习时间（小时）
    words_learned = Column(Integer, default=0)     # 已学单词数
    articles_read = Column(Integer, default=0)     # 已读文章数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="user_profile")

class UserLanguage(Base):
    __tablename__ = "user_languages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    language = Column(String, nullable=False)  # 语言名称
    level = Column(String, default="A1")       # 语言级别 (A1, A2, B1, B2, C1, C2)
    progress = Column(Float, default=0.0)      # 进度百分比
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="languages")

class UserStatistics(Base):
    __tablename__ = "user_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    study_time = Column(Integer, default=0)  # 以分钟为单位
    words_learned = Column(Integer, default=0)
    articles_read = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="statistics")

class UserLearningHistory(Base):
    __tablename__ = "user_learning_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String, nullable=False)  # 例如：阅读、听力、词汇学习
    title = Column(String)
    language = Column(String)
    level = Column(String)
    duration = Column(Integer)  # 以分钟为单位
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="learning_history")

class UserVocabulary(Base):
    __tablename__ = "user_vocabulary"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    language = Column(String, nullable=False)
    example = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    mastery_level = Column(Integer, default=0)  # 掌握程度 (0-5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="vocabulary")
