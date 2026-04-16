import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # ========== 数据库配置 ==========
    # 数据库类型：sqlite 或 postgresql
    DATABASE_TYPE = os.environ.get("DATABASE_TYPE", "sqlite")
    
    # SQLite 配置
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "sqlite:///course_selection.db"
    )
    
    # PostgreSQL 配置
    DATABASE_HOST = os.environ.get("DATABASE_HOST", "localhost")
    DATABASE_PORT = int(os.environ.get("DATABASE_PORT", 5432))
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "course_selection")
    DATABASE_USER = os.environ.get("DATABASE_USER", "course_user")
    DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "course123")
    
    # 构建 PostgreSQL 连接 URI
    POSTGRESQL_URI = (
        f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}"
        f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )
    
    # 根据 DATABASE_TYPE 选择数据库
    if DATABASE_TYPE == "postgresql":
        SQLALCHEMY_DATABASE_URI = POSTGRESQL_URI

    # SQLAlchemy 配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 50,          # 连接池大小
        "pool_recycle": 3600,     # 连接回收时间（秒）
        "pool_pre_ping": True,    # 连接前检查
        "max_overflow": 100       # 最大溢出连接数
    }

    # ========== Redis 配置 ==========
    REDIS_HOST = os.environ.get("REDIS_HOST") or "localhost"
    REDIS_PORT = int(os.environ.get("REDIS_PORT") or 6379)
    REDIS_DB = int(os.environ.get("REDIS_DB") or 0)
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD") or None

    # ========== Session 配置 ==========
    # 使用 Redis 存储 Session（生产环境推荐）
    SESSION_TYPE = "redis"
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = "session:"
    SESSION_REDIS_HOST = REDIS_HOST
    SESSION_REDIS_PORT = REDIS_PORT
    SESSION_REDIS_DB = REDIS_DB
    SESSION_REDIS_PASSWORD = REDIS_PASSWORD
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # ========== 选课配置 ==========
    COURSE_SELECTION_DURATION = 30 * 60  # 30 分钟（秒）
    MAX_COURSE_CAPACITY = 90  # 每门课程最大人数
    MIN_COURSE_CAPACITY = 30  # 每门课程最低人数

    # ========== 限流配置 - 针对 800 人并发优化 ==========
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_MAX_REQUESTS = 500  # 每秒最大请求数
    RATE_LIMIT_WINDOW = 1  # 时间窗口（秒）
    
    # ========== 高并发配置 ==========
    DATABASE_TIMEOUT = 30.0  # 数据库超时时间（秒）
    DATABASE_BUSY_TIMEOUT = 5000  # SQLite busy 超时（毫秒）
    MAX_QUEUE_SIZE = 1000  # 最大选课队列长度
    
    # ========== Redis 锁配置 ==========
    REDIS_LOCK_TIMEOUT = 10  # 锁超时时间（秒）
    REDIS_LOCK_BLOCKING_TIMEOUT = 5  # 获取锁的阻塞超时（秒）
