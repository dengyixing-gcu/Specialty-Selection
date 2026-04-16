from flask import Flask, redirect, url_for
from flask_session import Session
import redis
from config import Config
from app.models import db

redis_client = None


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化 SQLAlchemy
    db.init_app(app)

    # 初始化 Redis
    global redis_client
    redis_client = redis.Redis(
        host=app.config.get("SESSION_REDIS_HOST") or app.config.get("REDIS_HOST", "localhost"),
        port=app.config.get("SESSION_REDIS_PORT") or app.config.get("REDIS_PORT", 6379),
        db=app.config.get("SESSION_REDIS_DB") or app.config.get("REDIS_DB", 0),
        password=app.config.get("SESSION_REDIS_PASSWORD") or app.config.get("REDIS_PASSWORD"),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )

    # 初始化 Session（使用 Redis 存储）
    Session(app)

    # 注册蓝图
    from app.routes import auth, courses, selection, admin, auto_assign

    app.register_blueprint(auth.bp)
    app.register_blueprint(courses.bp)
    app.register_blueprint(selection.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(auto_assign.bp)

    # 根路由
    @app.route("/")
    def index():
        return redirect(url_for('auth.login'))

    # 注册错误处理
    @app.errorhandler(404)
    def not_found_error(error):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error"}, 500

    return app


def get_redis():
    return redis_client
