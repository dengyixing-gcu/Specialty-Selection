#!/bin/bash
set -e

# 启动 Redis
redis-server --daemonize yes

# 等待 Redis 启动
sleep 2

# 初始化数据库
python -c "from app.models import init_db; init_db()"

# 启动应用
exec gunicorn --bind 0.0.0.0:5000 --workers 4 "run:app"
