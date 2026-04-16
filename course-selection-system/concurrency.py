"""
高并发模块 - 使用 Redis 分布式锁
支持 SQLite 和 PostgreSQL
"""

import threading
import time
import sqlite3
from collections import defaultdict
from datetime import datetime
from functools import wraps
from flask import jsonify, request, session
from config import Config
from app import get_redis

# 全局锁（SQLite 备用）
db_lock = threading.Lock()
course_locks = defaultdict(threading.Lock)
rate_limit_lock = threading.Lock()

# 限流配置
RATE_LIMIT_ENABLED = Config.RATE_LIMIT_ENABLED
RATE_LIMIT_MAX_REQUESTS = Config.RATE_LIMIT_MAX_REQUESTS
RATE_LIMIT_WINDOW = Config.RATE_LIMIT_WINDOW
RATE_LIMIT_STORE = defaultdict(list)


def check_rate_limit(client_ip):
    """检查请求频率限制"""
    if not RATE_LIMIT_ENABLED:
        return True, 0
    
    with rate_limit_lock:
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW
        
        RATE_LIMIT_STORE[client_ip] = [
            t for t in RATE_LIMIT_STORE[client_ip] if t > window_start
        ]
        
        if len(RATE_LIMIT_STORE[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return False, len(RATE_LIMIT_STORE[client_ip])
        
        RATE_LIMIT_STORE[client_ip].append(now)
        return True, len(RATE_LIMIT_STORE[client_ip])


def rate_limit(f):
    """限流装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr or '127.0.0.1'
        allowed, count = check_rate_limit(client_ip)
        
        if not allowed:
            return jsonify({
                "error": f"请求过于频繁，请等待 {RATE_LIMIT_WINDOW} 秒",
                "retry_after": RATE_LIMIT_WINDOW
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function


def get_redis_lock(course_id):
    """获取 Redis 分布式锁"""
    redis_client = get_redis()
    if not redis_client:
        return None
    
    lock_key = f"course_lock:{course_id}"
    return redis_client.lock(
        lock_key,
        timeout=Config.REDIS_LOCK_TIMEOUT,
        blocking_timeout=Config.REDIS_LOCK_BLOCKING_TIMEOUT
    )


def atomic_select_course_with_redis(student_id, course_id):
    """使用 Redis 分布式锁的原子性选课操作"""
    from app.models import db, Selection, Course
    from sqlalchemy.exc import IntegrityError
    
    redis_client = get_redis()
    
    if not redis_client:
        # Redis 不可用，降级到数据库锁
        return atomic_select_course_with_db_lock(student_id, course_id)
    
    lock_key = f"course_lock:{course_id}"
    lock = redis_client.lock(
        lock_key,
        timeout=Config.REDIS_LOCK_TIMEOUT,
        blocking_timeout=Config.REDIS_LOCK_BLOCKING_TIMEOUT
    )
    
    if not lock.acquire():
        return False, "系统繁忙，请稍后重试"
    
    try:
        # 检查是否已选课
        existing = Selection.query.filter_by(student_id=student_id).first()
        if existing:
            return False, "您已选择课程"
        
        # 获取课程信息（加锁后再次检查）
        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return False, "课程不存在"
        
        if course.current_count >= course.max_capacity:
            return False, "课程已满"
        
        # 创建选课记录
        selection = Selection(
            student_id=student_id,
            course_id=course_id,
            confirmed=True
        )
        db.session.add(selection)
        
        # 更新课程人数
        course.current_count += 1
        db.session.commit()
        
        return True, "选课成功"
        
    except IntegrityError:
        db.session.rollback()
        return False, "您已选择课程"
    except Exception as e:
        db.session.rollback()
        return False, f"选课失败：{str(e)}"
    finally:
        lock.release()


def atomic_select_course_with_db_lock(student_id, course_id):
    """使用数据库锁的原子性选课操作（PostgreSQL/SQLite）"""
    from app.models import db, Selection, Course
    from sqlalchemy.exc import IntegrityError
    
    # 使用课程级锁
    course_lock = course_locks[course_id]
    
    with course_lock:
        try:
            # 检查是否已选课
            existing = Selection.query.filter_by(student_id=student_id).first()
            if existing:
                return False, "您已选择课程"
            
            # 获取课程信息
            course = Course.query.filter_by(id=course_id).with_for_update().first()
            if not course:
                return False, "课程不存在"
            
            if course.current_count >= course.max_capacity:
                return False, "课程已满"
            
            # 创建选课记录
            selection = Selection(
                student_id=student_id,
                course_id=course_id,
                confirmed=True
            )
            db.session.add(selection)
            
            # 更新课程人数
            course.current_count += 1
            db.session.commit()
            
            return True, "选课成功"
            
        except IntegrityError:
            db.session.rollback()
            return False, "您已选择课程"
        except Exception as e:
            db.session.rollback()
            return False, f"选课失败：{str(e)}"


def atomic_select_course(student_id, course_id):
    """
    原子性选课操作
    优先使用 Redis 分布式锁，降级到数据库锁
    """
    redis_client = get_redis()
    
    if redis_client:
        try:
            # 测试 Redis 连接
            redis_client.ping()
            return atomic_select_course_with_redis(student_id, course_id)
        except Exception:
            pass
    
    # Redis 不可用，使用数据库锁
    return atomic_select_course_with_db_lock(student_id, course_id)


class SelectionQueue:
    """选课队列（备用机制）"""
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
        self.processing = False
    
    def add(self, student_id, course_id, priority=0):
        with self.lock:
            self.queue.append({
                'student_id': student_id,
                'course_id': course_id,
                'priority': priority,
                'timestamp': time.time(),
                'status': 'pending'
            })
            self.queue.sort(key=lambda x: (-x['priority'], x['timestamp']))
            return len(self.queue)
    
    def process_next(self):
        with self.lock:
            if not self.queue:
                return None
            return self.queue.pop(0)
    
    def get_position(self, student_id):
        with self.lock:
            for i, item in enumerate(self.queue):
                if item['student_id'] == student_id:
                    return i + 1
            return 0
    
    def size(self):
        with self.lock:
            return len(self.queue)


selection_queue = SelectionQueue()
