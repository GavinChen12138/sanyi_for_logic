"""
school_loader.py — 高校 JSON 数据加载、内存缓存、热重载
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)

# 全局缓存：学校数据列表
_schools_data: list[dict] = []
_lock = Lock()


def load_schools(file_path: str) -> list[dict]:
    """从 JSON 文件加载学校数据到内存"""
    global _schools_data
    path = Path(file_path)
    if not path.exists():
        logger.warning("学校数据文件不存在: %s", file_path)
        return []

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    with _lock:
        _schools_data = data

    school_count = len(data)
    group_count = sum(len(s.get("groups", [])) for s in data)
    logger.info("已加载学校数据: %d 所院校, %d 个专业组", school_count, group_count)
    return data


def get_schools() -> list[dict]:
    """获取当前内存中的学校数据"""
    with _lock:
        return _schools_data


def reload_schools(file_path: str) -> list[dict]:
    """热重载学校数据（回滚或上传后调用，无需重启进程）"""
    logger.info("热重载学校数据: %s", file_path)
    return load_schools(file_path)


def count_schools_and_groups(data: list[dict]) -> tuple[int, int]:
    """统计院校数量和专业组数量"""
    school_count = len(data)
    group_count = sum(len(s.get("groups", [])) for s in data)
    return school_count, group_count
