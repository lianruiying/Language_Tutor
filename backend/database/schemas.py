from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr

# 共享属性
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True

# 创建用户时需要的属性
class UserCreate(UserBase):
    email: EmailStr
    username: str
    password: str

# 更新用户时可以更新的属性
class UserUpdate(UserBase):
    password: Optional[str] = None
    avatar: Optional[str] = None

# 用户语言
class UserLanguageBase(BaseModel):
    language: str
    level: Optional[str] = "A1"
    progress: Optional[float] = 0.0

class UserLanguageCreate(UserLanguageBase):
    pass

class UserLanguage(UserLanguageBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# 用户资料
class UserProfileBase(BaseModel):
    total_study_time: Optional[float] = 0.0
    words_learned: Optional[int] = 0
    articles_read: Optional[int] = 0

class UserProfileCreate(UserProfileBase):
    pass

class UserProfile(UserProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# 学习历史
class LearningHistoryBase(BaseModel):
    activity_type: str
    title: str
    description: Optional[str] = None
    language: str
    level: Optional[str] = None
    duration: Optional[float] = 0.0

class LearningHistoryCreate(LearningHistoryBase):
    pass

class LearningHistory(LearningHistoryBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# 用户词汇
class UserVocabularyBase(BaseModel):
    word: str
    translation: str
    language: str
    example: Optional[str] = None
    notes: Optional[str] = None
    mastery_level: Optional[int] = 0

class UserVocabularyCreate(UserVocabularyBase):
    pass

class UserVocabulary(UserVocabularyBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# 数据库中存储的用户信息
class UserInDBBase(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    avatar: Optional[str] = None

    class Config:
        orm_mode = True

# 返回给API的用户信息
class User(UserInDBBase):
    pass

# 返回给API的详细用户信息
class UserDetailed(User):
    profile: Optional[UserProfile] = None
    learning_languages: Optional[List[UserLanguage]] = []
    learning_history: Optional[List[LearningHistory]] = []

# 存储在数据库中的用户信息（包含密码哈希）
class UserInDB(UserInDBBase):
    hashed_password: str

# Token模型
class Token(BaseModel):
    access_token: str
    token_type: str

# Token载荷
class TokenPayload(BaseModel):
    sub: Optional[int] = None
    exp: Optional[int] = None

# 用户统计数据
class UserStatisticsBase(BaseModel):
    study_time: Optional[int] = 0
    words_learned: Optional[int] = 0
    articles_read: Optional[int] = 0


class UserStatisticsCreate(UserStatisticsBase):
    user_id: int


class UserStatisticsUpdate(UserStatisticsBase):
    pass


class UserStatistics(UserStatisticsBase):
    id: int
    user_id: int
    updated_at: datetime

    class Config:
        orm_mode = True


# 用户学习历史
class UserLearningHistoryBase(BaseModel):
    activity_type: str
    title: Optional[str] = None
    language: Optional[str] = None
    level: Optional[str] = None
    duration: Optional[int] = None


class UserLearningHistoryCreate(UserLearningHistoryBase):
    user_id: int


class UserLearningHistoryUpdate(UserLearningHistoryBase):
    pass


class UserLearningHistory(UserLearningHistoryBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# 用户资料响应模型
class UserProfileResponse(BaseModel):
    username: str
    email: EmailStr
    avatar: Optional[str] = None
    learningLanguages: List[str] = []
    level: Dict[str, str] = {}
    studyTime: int = 0
    wordsLearned: int = 0
    articlesRead: int = 0


# 用户资料更新模型
class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
    learningLanguages: Optional[List[str]] = None
    level: Optional[Dict[str, str]] = None


# 用户历史响应模型
class UserHistoryResponse(BaseModel):
    id: int
    activity_type: str
    title: Optional[str] = None
    language: Optional[str] = None
    level: Optional[str] = None
    duration: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True 