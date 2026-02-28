"""
routers/super.py — 高校数据管理接口（仅 super_admin）
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from deps import require_super
from models import User, SchoolDataVersion
from schemas import ApiResponse, EditGroupRequest
from school_loader import reload_schools, count_schools_and_groups, get_schools
from crud import (
    get_all_versions,
    get_next_version_no,
    create_version,
    rollback_version as crud_rollback_version,
    get_version_by_id,
    get_user_by_id,
)

router = APIRouter(prefix="/api/super", tags=["数据管理"])

# 数据目录
DATA_DIR = Path(settings.data_dir)


def _ensure_data_dir():
    """确保数据目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _validate_schools_json(data: list) -> list[str]:
    """校验高校 JSON 数据格式，返回错误列表"""
    errors = []

    if not isinstance(data, list):
        return ["顶层必须是数组"]

    for i, school in enumerate(data):
        prefix = f"第 {i + 1} 个学校"

        # 检查学校必填字段
        for field in ("id", "name", "groups"):
            if field not in school:
                errors.append(f"{prefix} 缺少 {field} 字段")

        if "groups" not in school:
            continue

        for j, group in enumerate(school.get("groups", [])):
            g_prefix = f"{prefix} 第 {j + 1} 个专业组"

            # 检查专业组必填字段
            for field in ("id", "name", "rules", "entry_rule", "required_subjects"):
                if field not in group:
                    errors.append(f"{g_prefix} 缺少 {field} 字段")

            # 检查 rules 五个键
            rules = group.get("rules", {})
            for grade in ("A", "B", "C", "D", "E"):
                if grade not in rules:
                    errors.append(f"{g_prefix} rules 缺少 {grade} 键")

            # 检查 entry_rule
            entry_rule = group.get("entry_rule", {})
            if "kind" not in entry_rule:
                errors.append(f"{g_prefix} entry_rule 缺少 kind 字段")
            if "score" not in entry_rule:
                errors.append(f"{g_prefix} entry_rule 缺少 score 字段")

            # 检查 required_subjects_mode
            mode = group.get("required_subjects_mode")
            if mode is not None and mode not in ("and", "or"):
                errors.append(f"{g_prefix} required_subjects_mode 必须为 and 或 or")

    return errors


@router.get("/schools/versions", response_model=ApiResponse)
async def get_versions(
    current_user: User = Depends(require_super),
    db: Session = Depends(get_db),
):
    """获取数据版本历史列表"""
    versions = get_all_versions(db)
    result = []
    for v in versions:
        uploader = get_user_by_id(db, v.uploaded_by)
        result.append({
            "id": v.id,
            "version_no": v.version_no,
            "school_count": v.school_count,
            "group_count": v.group_count,
            "note": v.note,
            "uploaded_by": v.uploaded_by,
            "uploaded_by_name": uploader.name if uploader else "未知",
            "uploaded_at": v.uploaded_at.isoformat() if v.uploaded_at else None,
            "is_active": bool(v.is_active),
        })
    return ApiResponse(data=result)


@router.post("/schools/upload", response_model=ApiResponse)
async def upload_schools(
    file: UploadFile = File(...),
    note: str = Form(default=""),
    current_user: User = Depends(require_super),
    db: Session = Depends(get_db),
):
    """上传新的 schools.json（含格式校验）"""
    # 读取文件内容
    content = await file.read()

    # 步骤 1: 解析 JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return ApiResponse(code=4020, msg=f"JSON 解析失败: {str(e)}")

    # 步骤 2: 格式校验
    errors = _validate_schools_json(data)
    if errors:
        return ApiResponse(code=4020, msg="数据校验失败", data=errors)

    # 步骤 3: 校验通过后写入文件
    _ensure_data_dir()
    version_no = get_next_version_no(db)
    file_name = f"v{version_no}_schools.json"
    file_path = str(DATA_DIR / file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 步骤 4: 入库
    school_count, group_count = count_schools_and_groups(data)
    version = create_version(
        db=db,
        version_no=version_no,
        file_path=file_path,
        school_count=school_count,
        group_count=group_count,
        note=note or f"上传新版本 v{version_no}",
        uploaded_by=current_user.id,
    )

    # 步骤 5: 热重载内存数据
    reload_schools(file_path)

    return ApiResponse(
        msg=f"上传成功，已生效为 v{version_no}",
        data={"version_no": version_no, "school_count": school_count, "group_count": group_count},
    )


@router.post("/schools/versions/{version_id}/rollback", response_model=ApiResponse)
async def rollback_to_version(
    version_id: int,
    current_user: User = Depends(require_super),
    db: Session = Depends(get_db),
):
    """回滚到指定版本"""
    version = crud_rollback_version(db, version_id)
    if version is None:
        return ApiResponse(code=4004, msg="版本不存在")

    # 热重载
    reload_schools(version.file_path)
    return ApiResponse(msg=f"已回滚到 v{version.version_no}")


@router.get("/schools/versions/{version_id}/download", response_model=None)
async def download_version(
    version_id: int,
    current_user: User = Depends(require_super),
    db: Session = Depends(get_db),
):
    """下载指定版本的 JSON 文件"""
    version = get_version_by_id(db, version_id)
    if version is None:
        return ApiResponse(code=4004, msg="版本不存在")

    file_path = Path(version.file_path)
    if not file_path.exists():
        return ApiResponse(code=5000, msg="文件不存在")

    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(file_path),
        filename=f"v{version.version_no}_schools.json",
        media_type="application/json",
    )


@router.put("/schools/{school_id}/groups/{group_id}", response_model=ApiResponse)
async def edit_group(
    school_id: str,
    group_id: str,
    body: EditGroupRequest,
    current_user: User = Depends(require_super),
    db: Session = Depends(get_db),
):
    """逐条编辑专业组数据"""
    schools_data = get_schools()
    if not schools_data:
        return ApiResponse(code=5000, msg="学校数据未加载")

    # 深拷贝当前数据
    import copy
    new_data = copy.deepcopy(schools_data)

    # 查找目标学校和专业组
    target_school = None
    target_group = None
    school_name = ""
    group_name = ""

    for school in new_data:
        if school["id"] == school_id:
            target_school = school
            school_name = school.get("name", school_id)
            for group in school.get("groups", []):
                if group["id"] == group_id:
                    target_group = group
                    group_name = group.get("name", group_id)
                    break
            break

    if target_school is None:
        return ApiResponse(code=4004, msg=f"院校 {school_id} 不存在")
    if target_group is None:
        return ApiResponse(code=4004, msg=f"专业组 {group_id} 不存在")

    # 应用修改
    update_fields = body.model_dump(exclude_none=True)
    if "entry_rule_score" in update_fields:
        target_group.setdefault("entry_rule", {})["score"] = update_fields.pop("entry_rule_score")
    if "entry_rule_text" in update_fields:
        target_group["entry_rule_text"] = update_fields.pop("entry_rule_text")

    for field, value in update_fields.items():
        target_group[field] = value

    # 保存为新版本
    _ensure_data_dir()
    version_no = get_next_version_no(db)
    file_name = f"v{version_no}_schools.json"
    file_path = str(DATA_DIR / file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    school_count, group_count = count_schools_and_groups(new_data)
    create_version(
        db=db,
        version_no=version_no,
        file_path=file_path,
        school_count=school_count,
        group_count=group_count,
        note=f"逐条编辑：{school_name}-{group_name}",
        uploaded_by=current_user.id,
    )

    # 热重载
    reload_schools(file_path)

    return ApiResponse(msg=f"编辑成功，已生成新版本 v{version_no}")


@router.get("/schools/list", response_model=ApiResponse)
async def get_schools_list(
    current_user: User = Depends(require_super),
):
    """获取当前学校列表（用于逐条编辑页面展示）"""
    schools_data = get_schools()
    if not schools_data:
        return ApiResponse(code=5000, msg="学校数据未加载")

    # 返回精简列表
    result = []
    for school in schools_data:
        groups = []
        for g in school.get("groups", []):
            groups.append({
                "id": g["id"],
                "name": g["name"],
                "entry_rule_text": g.get("entry_rule_text", ""),
                "preliminary_line": g.get("preliminary_line", 0),
                "admission_count": g.get("admission_count", 0),
            })
        result.append({
            "id": school["id"],
            "name": school["name"],
            "tags": school.get("tags", []),
            "groups": groups,
        })

    return ApiResponse(data=result)


@router.get("/schools/{school_id}/groups/{group_id}", response_model=ApiResponse)
async def get_group_detail(
    school_id: str,
    group_id: str,
    current_user: User = Depends(require_super),
):
    """获取单个专业组详情（用于编辑弹窗）"""
    schools_data = get_schools()
    for school in schools_data:
        if school["id"] == school_id:
            for group in school.get("groups", []):
                if group["id"] == group_id:
                    return ApiResponse(data={
                        "school_id": school_id,
                        "school_name": school["name"],
                        "group": group,
                    })
            return ApiResponse(code=4004, msg="专业组不存在")
    return ApiResponse(code=4004, msg="院校不存在")
