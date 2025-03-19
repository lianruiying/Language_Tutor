from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.core.config import Settings

# 创建 settings 实例
settings = Settings()

engine = create_engine(str(settings.DATABASE_URI))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 依赖项，用于获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 