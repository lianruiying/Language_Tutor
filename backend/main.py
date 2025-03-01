from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 检查必要的环境变量
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    error_message = "错误: 未找到 OPENAI_API_KEY 环境变量。请确保已创建 .env 文件并设置正确的 API Key。"
    logger.error(error_message)
    raise ValueError(error_message)

# 初始化 FastAPI 应用
app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://durian_lian.top
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建 OpenAI 客户端
try:
    client = OpenAI(api_key=api_key)
    logger.info("OpenAI 客户端初始化成功")
except Exception as e:
    logger.error(f"OpenAI 客户端初始化失败: {str(e)}")
    raise

class ChatMessage(BaseModel):
    message: str
    language: str

@app.post("/api/chat")
async def chat_with_ai(chat_input: ChatMessage):
    try:
        # 记录请求，但不记录具体内容以保护隐私
        logger.info(f"收到聊天请求，语言: {chat_input.language}")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """你现在是一个精通各种外语的老师，面对的学生主要为中国人，如果收到的需求主要为汉语，请以汉语回复，如果是其他语言，也用对应的语言回复。

任务：
学生会与你沟通，让你生成对应需求的外语小短文以供学习。
如果任务判定与外语学习无关，请不要理会，可以直接回复："此类任务与外语学习无关，不处理。"
如果任务与外语学习有关，请根据需求生成对应的外语小短文，小短文前后请另用空行隔开。"""
                },
                {
                    "role": "user",
                    "content": chat_input.message
                }
            ]
        )
        
        ai_response = response.choices[0].message.content
        # 记录响应长度而不是具体内容
        logger.info(f"AI 响应成功，响应长度: {len(ai_response)}")
        
        return {"response": ai_response}
    except Exception as e:
        error_msg = f"处理请求时发生错误: {type(e).__name__}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "服务器内部错误",  # 对外显示通用错误信息
                "type": type(e).__name__
            }
        )

@app.get("/")
async def root():
    return {"status": "ok", "message": "服务器正在运行"}

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