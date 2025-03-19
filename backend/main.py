from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import logging
from openai import OpenAI  # 使用OpenAI库来调用DeepSeek API
from dotenv import load_dotenv
import traceback
import uuid
import json
import re
import httpx
import asyncio
from pathlib import Path
import datetime

from backend.core.config import settings
from backend.api.auth import router as auth_router
from backend.api.users import router as users_router
from backend.database.database import Base, engine
from backend.api.api_v1.api import api_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 获取当前文件所在目录
BASE_DIR = Path(__file__).resolve().parent

# 加载环境变量
load_dotenv(BASE_DIR / '.env')

# 从环境变量获取API密钥
api_key = settings.DEEPSEEK_API_KEY
api_base = settings.DEEPSEEK_API_BASE

# 初始化DeepSeek客户端 - 使用OpenAI兼容接口
client = OpenAI(
    api_key=api_key,
    base_url=f"{api_base}/v1"  # DeepSeek API的基础URL
)

# 添加日志记录
logger.info(f"DeepSeek客户端初始化完成，使用base_url: {api_base}/v1")

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 初始化 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["认证"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["用户"])
app.include_router(api_router, prefix=settings.API_V1_STR)

# 定义聊天消息模型
class ChatMessage(BaseModel):
    message: str
    language: str = "chinese"  # 添加默认值

# 创建一个HTTP请求拦截器
class HTTPRequestLoggingMiddleware:
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            # 如果不是HTTP请求，直接传递给下一个中间件
            return await self.app(scope, receive, send)
            
        # 记录请求信息
        request_id = str(uuid.uuid4())
        path = scope.get("path", "")
        method = scope.get("method", "")
        
        logger.info(f"[{request_id}] 收到请求: {method} {path}")
        
        # 处理请求
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status = message.get("status", 0)
                logger.info(f"[{request_id}] 响应状态: {status}")
            await send(message)
            
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            logger.error(f"[{request_id}] 请求处理错误: {str(e)}")
            # 重新抛出异常，让FastAPI的异常处理器处理
            raise

# 添加中间件
app.add_middleware(HTTPRequestLoggingMiddleware)

@app.get("/test")
def test_endpoint():
    return {"status": "ok", "message": "API服务正常运行"}

@app.get("/test-deepseek")
async def test_deepseek_connection():
    try:
        # 尝试一个简单的API调用
        response = client.chat.completions.create(
            model="deepseek-chat",  # 使用DeepSeek的模型
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        return {"status": "success", "message": "DeepSeek API连接正常"}
    except Exception as e:
        logger.error(f"DeepSeek API连接测试失败: {str(e)}")
        return {"status": "error", "message": f"DeepSeek API连接失败: {str(e)}"}

@app.get("/test-models")
async def test_models():
    """测试可用模型"""
    try:
        # 直接使用httpx发送请求
        async with httpx.AsyncClient() as client:
            # 尝试获取模型列表
            response = await client.get(
                f"{api_base}/v1/models",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 404:
                # 如果models端点不存在，尝试使用chat/completions端点
                logger.info("Models端点不存在，尝试使用chat/completions端点")
                
                # 构建一个简单的请求来测试模型
                test_models = ["deepseek-chat", "deepseek-coder"]
                results = {}
                
                for model in test_models:
                    try:
                        test_response = await client.post(
                            f"{api_base}/v1/chat/completions",
                            json={
                                "model": model,
                                "messages": [{"role": "user", "content": "Hello"}],
                                "max_tokens": 5
                            },
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json"
                            }
                        )
                        
                        results[model] = {
                            "status_code": test_response.status_code,
                            "response": test_response.text[:100] if test_response.status_code == 200 else test_response.text
                        }
                    except Exception as model_error:
                        results[model] = {"error": str(model_error)}
                
                return {"status": "models_endpoint_not_found", "model_tests": results}
            
            return {
                "status": "success",
                "status_code": response.status_code,
                "models": response.json() if response.status_code == 200 else response.text
            }
    except Exception as e:
        logger.error(f"测试模型失败: {str(e)}")
        return {"status": "error", "message": str(e)}

# 修改chat接口的实现
@app.post("/api/chat")
async def chat_with_ai(chat_input: ChatMessage):
    try:
        # 打印客户端配置信息
        logger.info(f"收到聊天请求: {chat_input.message}")
        logger.info(f"选择语言: {chat_input.language}")
        
        # 打印API密钥信息（不显示完整密钥）
        if api_key:
            masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
            logger.info(f"API密钥状态: 已配置 (前缀: {masked_key})")
        else:
            logger.warning("API密钥状态: 未配置")
            return {"response": "API密钥未配置，请联系管理员", "status": "error"}
        
        # 构建消息
        messages = [
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
        ]
        
        # 尝试使用直接HTTP请求，避免使用客户端库可能导致的问题
        try:
            logger.info("使用直接HTTP请求调用DeepSeek API...")
            
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    f"{api_base}/v1/chat/completions",
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 2000
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                logger.info(f"API响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data["choices"][0]["message"]["content"]
                    
                    # 移除思维链内容
                    cleaned_response = re.sub(r'<think>.*?</think>', '', ai_response, flags=re.DOTALL)
                    cleaned_response = cleaned_response.strip()
                    
                    logger.info(f"处理后的响应: {cleaned_response[:100]}...")
                    
                    return {"response": cleaned_response, "status": "success"}
                else:
                    error_message = f"API错误: {response.status_code} {response.text}"
                    logger.error(error_message)
                    return {"response": error_message, "status": "error"}
                    
        except Exception as http_error:
            logger.error(f"HTTP请求错误: {str(http_error)}")
            
            # 尝试使用OpenAI客户端库
            try:
                logger.info("尝试使用OpenAI客户端库...")
                
                # 使用DeepSeek模型
                chat_completion = client.chat.completions.create(
                    model="deepseek-chat",  # 使用DeepSeek的模型
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                logger.info("API调用成功")
                
                # 获取响应
                ai_response = chat_completion.choices[0].message.content
                logger.info(f"原始响应: {ai_response[:100]}...")
                
                # 移除思维链内容
                cleaned_response = re.sub(r'<think>.*?</think>', '', ai_response, flags=re.DOTALL)
                cleaned_response = cleaned_response.strip()
                
                logger.info(f"处理后的响应: {cleaned_response[:100]}...")
                
                return {"response": cleaned_response, "status": "success"}
                
            except Exception as api_error:
                logger.error(f"API调用错误: {str(api_error)}")
                # 添加更详细的错误信息
                error_details = traceback.format_exc()
                logger.error(f"详细错误信息: {error_details}")
                
                return {"response": f"AI服务调用失败: {str(http_error)}\nAPI调用失败: {str(api_error)}", "status": "error"}
            
    except Exception as outer_e:
        logger.error(f"未预期的错误: {str(outer_e)}", exc_info=True)
        return {"response": f"服务器错误: {str(outer_e)}", "status": "error"}

@app.get("/debug")
def debug_info():
    """返回调试信息"""
    return {
        "api_key_configured": bool(api_key),
        "api_key_prefix": api_key[:4] + "..." if api_key else None,
        "routes": [
            {"path": route.path, "name": route.name, "methods": route.methods}
            for route in app.routes
        ]
    }


@app.get("/test-endpoints")
async def test_endpoints():
    """测试不同的API端点"""
    endpoints = [
        f"{api_base}/v1/chat/completions",
        "https://www.google.com",
        "https://www.baidu.com"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            async with httpx.AsyncClient() as client:
                if endpoint == f"{api_base}/v1/chat/completions":
                    # 对于API端点，使用POST请求
                    response = await client.post(
                        endpoint,
                        json={
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": "Hello"}],
                            "max_tokens": 5
                        },
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        timeout=10.0
                    )
                else:
                    # 对于其他URL，使用GET请求
                    response = await client.get(endpoint, timeout=10.0)
                
                results[endpoint] = {
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "response": response.text[:100] if response.status_code == 200 else response.text
                }
        except Exception as e:
            results[endpoint] = {
                "error": str(e)
            }
    
    return {
        "results": results
    }


@app.get("/test-models-list")
async def test_models_list():
    """测试不同的模型"""
    models = [
        "deepseek-chat",
        "deepseek-coder",
        "deepseek-lite"
    ]
    
    results = {}
    
    for model in models:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_base}/v1/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 5
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                
                results[model] = {
                    "status_code": response.status_code,
                    "response": response.text[:100] if response.status_code == 200 else response.text
                }
        except Exception as e:
            results[model] = {
                "error": str(e)
            }
    
    return {
        "results": results
    }

@app.get("/test-official-example")
async def test_official_example():
    """使用官方示例测试DeepSeek API"""
    try:
        # 使用官方示例代码
        completion = client.chat.completions.create(
            model="deepseek-chat",  # 使用DeepSeek的模型
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
        )
        
        return {
            "status": "success",
            "response": completion.choices[0].message.content,
            "model": completion.model,
            "usage": {
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/test-network")
async def test_network():
    """测试网络连接"""
    test_urls = [
        f"{api_base}/v1/chat/completions",
        "https://www.google.com",
        "https://www.baidu.com"
    ]
    
    results = {}
    
    for url in test_urls:
        try:
            async with httpx.AsyncClient() as client:
                if url == f"{api_base}/v1/chat/completions":
                    # 对于API端点，使用POST请求
                    response = await client.post(
                        url,
                        json={
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": "Hello"}],
                            "max_tokens": 5
                        },
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        timeout=10.0
                    )
                else:
                    # 对于其他URL，使用GET请求
                    response = await client.get(url, timeout=10.0)
                
                results[url] = {
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "response": response.text[:100] if response.status_code == 200 else response.text
                }
        except Exception as e:
            results[url] = {
                "error": str(e)
            }
    
    return {
        "results": results
    }


# 如果需要数据库 URL，直接使用：
# DATABASE_URL = settings.DATABASE_URI 

# 主入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug") 