"""
deps.py — FastAPI 依赖注入：角色权限守卫
"""
from __future__ import annotations

from fastapi import Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth import decode_token


def _extract_token(authorization: str = Header(default="")) -> str:
    """从 Authorization Header 提取 Bearer Token"""
    if authorization.startswith("Bearer "):
        return authorization[7:]
    return ""


def require_login(
    token: str = Depends(_extract_token),
    db: Session = Depends(get_db),
) -> User:
    """依赖：要求用户已登录，返回 User 对象"""
    if not token:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=200,
            detail={"code": 4010, "msg": "未提供认证令牌", "data": None},
        )

    payload = decode_token(token)
    if payload is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=200,
            detail={"code": 4010, "msg": "令牌无效或已过期", "data": None},
        )

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id, User.is_active == 1).first()
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=200,
            detail={"code": 4010, "msg": "用户不存在或已被禁用", "data": None},
        )
    return user


def require_admin(user: User = Depends(require_login)) -> User:
    """依赖：要求 admin 或 super_admin 角色"""
    if user.role not in ("admin", "super_admin"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=200,
            detail={"code": 4003, "msg": "权限不足，需要管理员权限", "data": None},
        )
    return user


def require_super(user: User = Depends(require_login)) -> User:
    """依赖：要求 super_admin 角色"""
    if user.role != "super_admin":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=200,
            detail={"code": 4003, "msg": "权限不足，需要超级管理员权限", "data": None},
        )
    return user
