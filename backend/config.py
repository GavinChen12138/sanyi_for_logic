"""
config.py — 全局配置管理，从环境变量 / .env 文件读取
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，所有可配置项集中管理"""

    # JWT
    jwt_secret: str = "change-me"
    jwt_expire_hours: int = 8
    jwt_algorithm: str = "HS256"

    # 匹配容差
    gaokao_near_gap: int = 10
    xuekao_near_gap: int = 5

    # 数据目录
    data_dir: str = "data/schools"

    # 数据库
    database_url: str = "sqlite:///./sanyi.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
