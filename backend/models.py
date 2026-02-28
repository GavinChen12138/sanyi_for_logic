"""
models.py — ORM 模型定义（User、SchoolDataVersion）
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)          # bcrypt hash
    name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="planner")
    # 可选值: "super_admin" | "admin" | "planner"
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class SchoolDataVersion(Base):
    """高校数据版本表"""
    __tablename__ = "school_data_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_no = Column(Integer, nullable=False)       # 自增版本号
    file_path = Column(String, nullable=False)         # JSON 文件路径
    school_count = Column(Integer, nullable=False)     # 院校数量
    group_count = Column(Integer, nullable=False)      # 专业组数量
    note = Column(String)                              # 更新备注
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, nullable=False, default=0)
    # 1=当前使用版本，同时只有一条记录为 1
