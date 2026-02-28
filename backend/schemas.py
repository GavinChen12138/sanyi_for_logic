"""
schemas.py — Pydantic v2 请求/响应数据模型
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator


# ── 通用响应包装 ──────────────────────────────────────────

class ApiResponse(BaseModel):
    """统一 API 响应格式"""
    code: int = 0
    msg: str = "ok"
    data: Any = None


# ── 认证相关 ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class UserInfo(BaseModel):
    """用户信息（不含密码）"""
    id: int
    username: str
    name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginData(BaseModel):
    """登录成功返回数据"""
    token: str
    user: UserInfo


# ── 账号管理相关 ──────────────────────────────────────────

class UserCreate(BaseModel):
    """创建账号请求"""
    username: str
    password: str
    name: str
    role: str = "planner"

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v: str) -> str:
        if v not in ("super_admin", "admin", "planner"):
            raise ValueError("角色值无效，必须为 super_admin / admin / planner")
        return v


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 4:
            raise ValueError("密码长度不能少于4位")
        return v


class ChangeRoleRequest(BaseModel):
    """修改角色请求"""
    new_role: str

    @field_validator("new_role")
    @classmethod
    def role_must_be_valid(cls, v: str) -> str:
        if v not in ("super_admin", "admin", "planner"):
            raise ValueError("角色值无效")
        return v


class ChangeStatusRequest(BaseModel):
    """启用/禁用请求"""
    is_active: bool


# ── 匹配相关 ─────────────────────────────────────────────

class MatchRequest(BaseModel):
    """成绩录入请求"""
    selected_subjects: list[str]
    xuekao_grades: dict[str, str]

    @field_validator("selected_subjects")
    @classmethod
    def subjects_count(cls, v: list[str]) -> list[str]:
        if len(v) != 3:
            raise ValueError("必须选择3门选考科目")
        valid = {"物理", "化学", "生物", "历史", "地理", "政治", "技术"}
        for s in v:
            if s not in valid:
                raise ValueError(f"无效的选考科目: {s}")
        return v

    @field_validator("xuekao_grades")
    @classmethod
    def grades_valid(cls, v: dict[str, str]) -> dict[str, str]:
        valid_grades = {"A", "B", "C", "D", "E"}
        required_subjects = {"语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治", "技术"}
        
        missing = required_subjects - set(v.keys())
        if missing:
            raise ValueError(f"缺少必填学考科目: {', '.join(missing)}")
            
        for subject, grade in v.items():
            if grade not in valid_grades:
                raise ValueError(f"{subject} 的学考等级无效，必须为 A/B/C/D/E")
        return v


# ── 数据版本相关 ───────────────────────────────────────────

class VersionInfo(BaseModel):
    """数据版本信息"""
    id: int
    version_no: int
    school_count: int
    group_count: int
    note: Optional[str] = None
    uploaded_by: int
    uploaded_by_name: Optional[str] = None
    uploaded_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UploadNoteRequest(BaseModel):
    """上传备注"""
    note: str = ""


class EditGroupRequest(BaseModel):
    """逐条编辑专业组请求"""
    preliminary_line: Optional[float] = None
    entry_rule_score: Optional[float] = None
    entry_rule_text: Optional[str] = None
    rules: Optional[dict[str, float]] = None
    required_subjects: Optional[list[str]] = None
    required_subjects_mode: Optional[str] = None
    last_year_composite_score: Optional[float] = None
    admission_count: Optional[int] = None
    description: Optional[str] = None

    @field_validator("required_subjects_mode")
    @classmethod
    def mode_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("and", "or"):
            raise ValueError("required_subjects_mode 必须为 and 或 or")
        return v
