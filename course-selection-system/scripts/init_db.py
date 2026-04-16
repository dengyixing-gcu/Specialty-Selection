"""
数据库初始化脚本 - 支持 SQLite 和 PostgreSQL
"""

import sys
from app import create_app
from app.models import db, init_db
from config import Config

def init():
    """初始化数据库"""
    app = create_app()
    
    with app.app_context():
        print(f"数据库类型：{Config.DATABASE_TYPE}")
        print(f"数据库 URI: {Config.SQLALCHEMY_DATABASE_URI}")
        
        # 创建所有表
        db.create_all()
        print("数据库表已创建")
        
        # 初始化数据
        init_db()
        print("初始数据已加载")
        
        print("\n数据库初始化完成！")

if __name__ == "__main__":
    init()
