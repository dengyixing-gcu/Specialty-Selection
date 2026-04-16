import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # SQLite 数据库配置
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "sqlite:///course_selection.db"
    )

    # Redis 配置
    REDIS_HOST = os.environ.get("REDIS_HOST") or "localhost"
    REDIS_PORT = int(os.environ.get("REDIS_PORT") or 6379)
    REDIS_DB = int(os.environ.get("REDIS_DB") or 0)

    # Session 配置
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = "session:"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # 选课配置
    COURSE_SELECTION_DURATION = 30 * 60  # 30 分钟（秒）
    MAX_COURSE_CAPACITY = 90  # 每门课程最大人数
    MIN_COURSE_CAPACITY = 30  # 每门课程最低人数

    # 限流配置
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_MAX_REQUESTS = 100  # 每秒最大请求数
    RATE_LIMIT_WINDOW = 1  # 时间窗口（秒）
