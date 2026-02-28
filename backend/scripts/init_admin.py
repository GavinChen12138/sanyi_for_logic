"""
scripts/init_admin.py — 初始化第一个超级管理员账号
使用方式: cd backend && python scripts/init_admin.py
"""

import sys
from pathlib import Path

# 将 backend 目录加入 sys.path
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from database import engine, Base, SessionLocal
from models import User
from auth import hash_password
from crud import get_user_by_username

# 默认超级管理员信息
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"
DEFAULT_NAME = "超级管理员"


def init_super_admin():
    """创建初始超级管理员账号"""
    # 建表（如果不存在）
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 检查是否已有 super_admin
        existing = get_user_by_username(db, DEFAULT_USERNAME)
        if existing:
            print(f"用户 '{DEFAULT_USERNAME}' 已存在（角色: {existing.role}），跳过创建")
            return

        # 创建 super_admin
        user = User(
            username=DEFAULT_USERNAME,
            password=hash_password(DEFAULT_PASSWORD),
            name=DEFAULT_NAME,
            role="super_admin",
        )
        db.add(user)
        db.commit()
        print(f"✅ 超级管理员创建成功")
        print(f"   用户名: {DEFAULT_USERNAME}")
        print(f"   密码:   {DEFAULT_PASSWORD}")
        print(f"   ⚠️  请登录后立即修改密码！")
    finally:
        db.close()


if __name__ == "__main__":
    init_super_admin()
