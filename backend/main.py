"""
main.py — FastAPI 应用入口，注册路由，启动时加载学校数据
"""

import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import engine, Base
from models import User, SchoolDataVersion
from school_loader import load_schools
from crud import get_active_version
from database import SessionLocal

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _load_initial_data():
    """启动时加载当前活跃版本的学校数据"""
    db = SessionLocal()
    try:
        version = get_active_version(db)
        if version:
            logger.info(
                "加载活跃版本 v%d: %s", version.version_no, version.file_path
            )
            load_schools(version.file_path)
        else:
            logger.warning("数据库中没有活跃的学校数据版本")
            # 尝试加载项目根目录的 schools.json 作为默认数据
            import os
            default_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "schools.json"
            )
            if os.path.exists(default_path):
                logger.info("加载默认学校数据: %s", default_path)
                load_schools(default_path)
            else:
                logger.warning("未找到默认学校数据文件")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：建表 + 加载数据
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表已就绪")
    _load_initial_data()
    yield
    # 关闭时（可扩展清理逻辑）
    logger.info("应用关闭")


app = FastAPI(
    title="三位一体筛查工具 API",
    description="浙江三位一体快速筛查工具后端接口",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置（开发环境允许前端 localhost 访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理：统一返回格式
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """捕获未处理的异常，统一返回 5000 错误码"""
    logger.error("未处理的异常: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=200,
        content={"code": 5000, "msg": "服务器内部错误", "data": None},
    )


# 注册路由
from routers.auth import router as auth_router
from routers.admin import router as admin_router
from routers.match import router as match_router

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(match_router)

# Phase 2 路由（数据管理）
try:
    from routers.super import router as super_router
    app.include_router(super_router)
except ImportError:
    logger.info("super 路由尚未实现，跳过注册")
