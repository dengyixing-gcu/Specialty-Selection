from flask import Flask
from flask_session import Session
import redis
from config import Config

redis_client = None


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化 Redis
    global redis_client
    redis_client = redis.Redis(
        host=app.config["REDIS_HOST"],
        port=app.config["REDIS_PORT"],
        db=app.config["REDIS_DB"],
        decode_responses=True,
    )

    # 初始化 Session
    Session(app)

    # 注册蓝图
    from app.routes import auth, courses, selection, admin, auto_assign

    app.register_blueprint(auth.bp)
    app.register_blueprint(courses.bp)
    app.register_blueprint(selection.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(auto_assign.bp)

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
