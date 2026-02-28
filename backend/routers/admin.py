"""
routers/admin.py — 账号管理接口（admin 和 super_admin 可用）
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from deps import require_admin
from models import User
from schemas import (
    ApiResponse,
    UserCreate,
    UserInfo,
    ResetPasswordRequest,
    ChangeRoleRequest,
    ChangeStatusRequest,
)
from crud import (
    get_users_for_admin,
    get_users_for_super,
    get_user_by_username,
    get_user_by_id,
    create_user,
    reset_user_password,
    change_user_role,
    change_user_status,
)

router = APIRouter(prefix="/api/admin", tags=["账号管理"])


@router.get("/users", response_model=ApiResponse)
async def get_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取账号列表：admin 看不到 super_admin 账号"""
    if current_user.role == "super_admin":
        users = get_users_for_super(db)
    else:
        users = get_users_for_admin(db)

    user_list = [UserInfo.model_validate(u).model_dump() for u in users]
    return ApiResponse(data=user_list)


@router.post("/users", response_model=ApiResponse)
async def create_new_user(
    body: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """创建账号：admin 只能创建 planner"""
    # admin 权限限制
    if current_user.role == "admin" and body.role != "planner":
        return ApiResponse(code=4003, msg="普通管理员只能创建规划师账号")

    # 用户名唯一性检查
    if get_user_by_username(db, body.username):
        return ApiResponse(code=4020, msg="用户名已存在")

    user = create_user(db, body.username, body.password, body.name, body.role)
    user_info = UserInfo.model_validate(user)
    return ApiResponse(data=user_info.model_dump(), msg="账号创建成功")


@router.put("/users/{user_id}/reset-password", response_model=ApiResponse)
async def reset_password(
    user_id: int,
    body: ResetPasswordRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """重置他人密码"""
    target = get_user_by_id(db, user_id)
    if target is None:
        return ApiResponse(code=4004, msg="用户不存在")

    # 不能修改自己
    if target.id == current_user.id:
        return ApiResponse(code=4003, msg="不能修改自己的密码，请使用修改密码功能")

    # admin 不能操作 super_admin
    if current_user.role == "admin" and target.role == "super_admin":
        return ApiResponse(code=4003, msg="权限不足")

    reset_user_password(db, target, body.new_password)
    return ApiResponse(msg="密码重置成功")


@router.put("/users/{user_id}/role", response_model=ApiResponse)
async def update_role(
    user_id: int,
    body: ChangeRoleRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """修改用户角色"""
    target = get_user_by_id(db, user_id)
    if target is None:
        return ApiResponse(code=4004, msg="用户不存在")

    # 不能修改自己
    if target.id == current_user.id:
        return ApiResponse(code=4003, msg="不能修改自己的角色")

    # admin 只能操作 planner <-> admin
    if current_user.role == "admin":
        if target.role == "super_admin":
            return ApiResponse(code=4003, msg="权限不足，无法操作超级管理员")
        if body.new_role == "super_admin":
            return ApiResponse(code=4003, msg="权限不足，无法设置超级管理员角色")

    change_user_role(db, target, body.new_role)
    return ApiResponse(msg="角色修改成功")


@router.put("/users/{user_id}/status", response_model=ApiResponse)
async def update_status(
    user_id: int,
    body: ChangeStatusRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """启用/禁用账号"""
    target = get_user_by_id(db, user_id)
    if target is None:
        return ApiResponse(code=4004, msg="用户不存在")

    # 不能禁用自己
    if target.id == current_user.id:
        return ApiResponse(code=4003, msg="不能修改自己的状态")

    # admin 不能操作 super_admin
    if current_user.role == "admin" and target.role == "super_admin":
        return ApiResponse(code=4003, msg="权限不足")

    change_user_status(db, target, body.is_active)
    status_text = "启用" if body.is_active else "禁用"
    return ApiResponse(msg=f"账号已{status_text}")
