from fastapi import APIRouter
from backend.api.auth import router as auth_router
from backend.api.users import router as users_router

api_router = APIRouter()

# 包含认证路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])

# 包含用户路由
api_router.include_router(users_router, prefix="/users", tags=["用户"]) 