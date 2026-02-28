"""
auth.py — JWT 生成与校验、密码哈希工具
"""
from __future__ import annotations

from datetime import datetime, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext

from config import settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """对明文密码进行 bcrypt 哈希"""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与哈希是否匹配"""
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int, role: str) -> str:
    """生成 JWT，payload 含 sub(用户ID) 和 role"""
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    """解码 JWT，成功返回 payload，失败返回 None"""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None
