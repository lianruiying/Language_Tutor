from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
import os
import logging

# 配置详细的日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()
logger.info("环境变量已加载")

# 初始化FastAPI应用
app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001"  # 添加 3001 端口
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS已配置")

# 配置OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("未找到OPENAI_API_KEY环境变量")
    raise ValueError("OpenAI API key not found")

# 创建OpenAI客户端
client = OpenAI(api_key=api_key)
logger.info("OpenAI客户端已初始化")

class ChatMessage(BaseModel):
    message: str
    language: str

@app.post("/api/chat")
async def chat_with_ai(chat_input: ChatMessage):
    try:
        logger.info(f"收到聊天请求: {chat_input.message}, 语言: {chat_input.language}")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"你是一位专业的{chat_input.language}语言教师。请用{chat_input.language}回答用户的问题，并帮助他们学习这门语言。"
                },
                {
                    "role": "user",
                    "content": chat_input.message
                }
            ]
        )
        
        ai_response = response.choices[0].message.content
        logger.info(f"AI回复: {ai_response}")
        
        return {"response": ai_response}
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "type": type(e).__name__
            }
        )

@app.get("/")
async def root():
    return {"status": "ok", "message": "服务器正在运行"}

@app.get("/test")
async def test_endpoint():
    try:
        return {
            "status": "ok", 
            "message": "API服务器正在运行",
            "openai_key_configured": bool(api_key)
        }
    except Exception as e:
        logger.error(f"测试端点错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 