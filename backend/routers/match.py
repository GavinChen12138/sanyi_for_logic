"""
routers/match.py — 成绩匹配接口
"""

import sys
from pathlib import Path

from fastapi import APIRouter, Depends

from deps import require_login
from models import User
from schemas import MatchRequest, ApiResponse
from school_loader import get_schools

# 将项目根目录加入 sys.path，以便导入 matcher.py
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from matcher import Matcher, StudentInput, result_to_dict

router = APIRouter(prefix="/api", tags=["匹配"])


@router.post("/match", response_model=ApiResponse)
async def match_schools(
    body: MatchRequest,
    current_user: User = Depends(require_login),
):
    """核心匹配接口：传入成绩数据，返回分级结果"""
    schools_data = get_schools()
    if not schools_data:
        return ApiResponse(code=5000, msg="学校数据未加载，请联系管理员")

    # 构造 matcher 输入
    student = StudentInput(
        selected_subjects=body.selected_subjects,
        xuekao_grades=body.xuekao_grades,
    )

    # 执行匹配
    matcher = Matcher(schools_data)
    results = matcher.match(student)

    # 序列化结果
    data = {
        status: [result_to_dict(r) for r in items]
        for status, items in results.items()
    }

    return ApiResponse(data=data)
