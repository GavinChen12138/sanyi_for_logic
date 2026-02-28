"""
crud.py — 数据库操作函数封装
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from models import User, SchoolDataVersion
from auth import hash_password


# ── 用户相关 ──────────────────────────────────────────────

def get_user_by_username(db: Session, username: str) -> User | None:
    """根据用户名查询用户"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """根据 ID 查询用户"""
    return db.query(User).filter(User.id == user_id).first()


def get_users_for_admin(db: Session) -> list[User]:
    """admin 查询用户列表：过滤掉 super_admin"""
    return (
        db.query(User)
        .filter(User.role != "super_admin")
        .order_by(User.created_at.desc())
        .all()
    )


def get_users_for_super(db: Session) -> list[User]:
    """super_admin 查询所有用户"""
    return db.query(User).order_by(User.created_at.desc()).all()


def create_user(
    db: Session, username: str, password: str, name: str, role: str
) -> User:
    """创建新用户"""
    user = User(
        username=username,
        password=hash_password(password),
        name=name,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def reset_user_password(db: Session, user: User, new_password: str) -> None:
    """重置用户密码"""
    user.password = hash_password(new_password)
    db.commit()


def change_user_role(db: Session, user: User, new_role: str) -> None:
    """修改用户角色"""
    user.role = new_role
    db.commit()


def change_user_status(db: Session, user: User, is_active: bool) -> None:
    """启用/禁用用户"""
    user.is_active = 1 if is_active else 0
    db.commit()


# ── 数据版本相关 ──────────────────────────────────────────

def get_active_version(db: Session) -> SchoolDataVersion | None:
    """获取当前活跃的数据版本"""
    return (
        db.query(SchoolDataVersion)
        .filter(SchoolDataVersion.is_active == 1)
        .first()
    )


def get_all_versions(db: Session) -> list[SchoolDataVersion]:
    """获取所有数据版本（按版本号降序）"""
    return (
        db.query(SchoolDataVersion)
        .order_by(SchoolDataVersion.version_no.desc())
        .all()
    )


def get_next_version_no(db: Session) -> int:
    """获取下一个版本号"""
    latest = (
        db.query(SchoolDataVersion)
        .order_by(SchoolDataVersion.version_no.desc())
        .first()
    )
    return (latest.version_no + 1) if latest else 1


def create_version(
    db: Session,
    version_no: int,
    file_path: str,
    school_count: int,
    group_count: int,
    note: str,
    uploaded_by: int,
) -> SchoolDataVersion:
    """创建新版本并设为活跃"""
    # 先将旧版本全部置为非活跃
    db.query(SchoolDataVersion).update({"is_active": 0})
    version = SchoolDataVersion(
        version_no=version_no,
        file_path=file_path,
        school_count=school_count,
        group_count=group_count,
        note=note,
        uploaded_by=uploaded_by,
        is_active=1,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def rollback_version(db: Session, version_id: int) -> SchoolDataVersion | None:
    """回滚到指定版本"""
    version = db.query(SchoolDataVersion).filter(
        SchoolDataVersion.id == version_id
    ).first()
    if version is None:
        return None
    db.query(SchoolDataVersion).update({"is_active": 0})
    version.is_active = 1
    db.commit()
    db.refresh(version)
    return version


def get_version_by_id(db: Session, version_id: int) -> SchoolDataVersion | None:
    """根据 ID 获取版本"""
    return db.query(SchoolDataVersion).filter(
        SchoolDataVersion.id == version_id
    ).first()
