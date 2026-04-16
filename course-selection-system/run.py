from app import create_app
from app.models import db, init_db
from waitress import serve

app = create_app()

if __name__ == "__main__":
    # 初始化数据库
    with app.app_context():
        db.create_all()
        init_db()
        print("数据库已初始化")
    
    # 高并发配置 - 支持 800+ 学生同时选课
    serve(
        app,
        host="0.0.0.0",
        port=5000,
        threads=200,           # 200 工作线程
        connection_limit=500   # 最大 500 并发连接
    )
