import os
from pathlib import Path
from dotenv import load_dotenv

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# 加载.env文件
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# 项目配置
PROJECT_NAME = "Language Tutor"
API_V1_STR = "/api/v1"

# 数据库配置
POSTGRES_SERVER = "114.55.128.59"  # 你的阿里云服务器IP
POSTGRES_USER = "lianruiying"
POSTGRES_PASSWORD = "LOLOLOLOL"
POSTGRES_DB = "language_tutor"
POSTGRES_PORT = "5432"
DATABASE_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

# 安全配置
SECRET_KEY = os.getenv("SECRET_KEY", "")
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7天

# GROQ API 配置
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_BASE = os.getenv("GROQ_API_BASE", "https://api.groq.com/v1")

# 创建一个设置对象，方便导入
class Settings:
    PROJECT_NAME = PROJECT_NAME
    API_V1_STR = API_V1_STR
    POSTGRES_SERVER = POSTGRES_SERVER
    POSTGRES_USER = POSTGRES_USER
    POSTGRES_PASSWORD = POSTGRES_PASSWORD
    POSTGRES_DB = POSTGRES_DB
    POSTGRES_PORT = POSTGRES_PORT
    DATABASE_URI = DATABASE_URI
    SECRET_KEY = SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES = ACCESS_TOKEN_EXPIRE_MINUTES
    GROQ_API_KEY = GROQ_API_KEY
    GROQ_API_BASE = GROQ_API_BASE

settings = Settings()

# 打印配置信息以便调试
print(f"数据库连接: {settings.DATABASE_URI}")
print(f"SECRET_KEY: {settings.SECRET_KEY[:5]}...") 