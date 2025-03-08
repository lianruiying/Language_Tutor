from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import logging
from groq import Groq
from dotenv import load_dotenv
import traceback
import uuid
import json
import re
import httpx
import asyncio
from pathlib import Path

from .core.config import settings
from .api import auth, users
from .database.database import Base, engine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 获取当前文件所在目录
BASE_DIR = Path(__file__).resolve().parent

# 加载环境变量
load_dotenv(BASE_DIR / '.env')

# 获取 API 密钥
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    error_message = "错误: 未找到 GROQ_API_KEY 环境变量。请确保已创建 .env 文件并设置正确的 API Key。"
    logger.error(error_message)
    raise ValueError(error_message)

# 初始化 Groq 客户端
client = Groq(api_key=api_key)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 初始化 FastAPI 应用
app = FastAPI(title=settings.PROJECT_NAME)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["认证"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["用户"])

class ChatMessage(BaseModel):
    message: str
    language: str = "english"

# 修改API基础URL和请求配置
base_url = "https://api.groq.com/openai/v1"

# 修改chat接口的实现
@app.post("/api/chat")
async def chat_with_ai(chat_input: ChatMessage):
    try:
        logger.info(f"收到聊天请求: {chat_input.message}")
        logger.info(f"选择语言: {chat_input.language if hasattr(chat_input, 'language') else '未指定'}")
        
        try:
            # 使用 Groq 客户端发送请求
            logger.info("正在调用 Groq API...")
            
            # 打印 API 密钥前几个字符（安全起见）
            if api_key:
                logger.info(f"使用 API 密钥: {api_key[:4]}...{api_key[-4:]}")
            else:
                logger.error("API 密钥为空")
                return {"response": "API 密钥未设置", "status": "error"}
            
            # 尝试调用 API
            try:
                chat_completion = client.chat.completions.create(
                    model="deepseek-r1-distill-llama-70b",
                    messages=[
                        {
                            "role": "system",
                            "content": """你是一位专业的语言教师。请按照以下方式回复：
1. 如果用户用中文提问，用中文回答；如果用户使用其他语言，用对应语言回答
2. 保持专业性和准确性
3. 根据用户水平调整内容难度
4. 如果需要思考，请将思考过程放在<think></think>标签中"""
                        },
                        {
                            "role": "user",
                            "content": chat_input.message
                        }
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                logger.info("Groq API 调用成功")
                
                # 获取响应
                ai_response = chat_completion.choices[0].message.content
                logger.info(f"原始响应: {ai_response[:100]}...")
                
                # 移除思维链内容
                cleaned_response = re.sub(r'<think>.*?</think>', '', ai_response, flags=re.DOTALL)
                cleaned_response = cleaned_response.strip()
                
                logger.info(f"处理后的响应: {cleaned_response[:100]}...")
                
                return {"response": cleaned_response, "status": "success"}
                
            except Exception as api_error:
                logger.error(f"API 调用错误: {str(api_error)}")
                return {"response": f"AI 服务调用失败: {str(api_error)}", "status": "error"}
                
        except Exception as e:
            logger.error(f"处理请求时发生错误: {str(e)}", exc_info=True)
            return {"response": f"服务器错误: {str(e)}", "status": "error"}
            
    except Exception as outer_e:
        logger.error(f"未预期的错误: {str(outer_e)}", exc_info=True)
        return {"response": f"服务器错误: {str(outer_e)}", "status": "error"}

@app.get("/")
def read_root():
    return {"message": "欢迎使用Language Tutor API"}

@app.get("/test")
async def test_endpoint():
    """
    测试端点，检查服务器状态和配置
    """
    try:
        return {
            "status": "ok",
            "message": "API 服务器正在运行",
            "api_configured": bool(api_key),  # 只返回是否配置，不返回具体值
        }
    except Exception as e:
        logger.error(f"测试端点错误: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

# 数据库配置
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_USER = os.getenv("POSTGRES_USER", "language_admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "your_secure_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "language_tutor")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# 数据库URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}" 