"""
routers/auth.py — 认证接口：登录、获取当前用户信息
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from deps import require_login
from models import User
from schemas import LoginRequest, UserInfo, LoginData, ApiResponse
from auth import verify_password, create_token
from crud import get_user_by_username

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=ApiResponse)
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    """登录接口：校验用户名密码，返回 JWT"""
    user = get_user_by_username(db, body.username)

    # 用户不存在或密码错误
    if user is None or not verify_password(body.password, user.password):
        return ApiResponse(code=4001, msg="用户名或密码错误")

    # 账号已禁用
    if not user.is_active:
        return ApiResponse(code=4001, msg="账号已被禁用，请联系管理员")

    # 生成 JWT
    token = create_token(user.id, user.role)
    user_info = UserInfo.model_validate(user)
    data = LoginData(token=token, user=user_info)
    return ApiResponse(data=data.model_dump())


@router.get("/me", response_model=ApiResponse)
async def get_me(current_user: User = Depends(require_login)):
    """获取当前登录用户信息"""
    user_info = UserInfo.model_validate(current_user)
    return ApiResponse(data=user_info.model_dump())
