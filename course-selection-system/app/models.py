"""
数据库模型 - 支持 SQLite 和 PostgreSQL
使用 SQLAlchemy ORM
"""

import hashlib
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

MAJORS = ["计算机科学与技术", "软件工程", "数据科学与大数据技术"]
CLASSES = ["1 班", "2 班", "3 班", "4 班"]

COURSES = [
    {"id": 1, "name": "企业数据资产管理"},
    {"id": 2, "name": "企业数字化运营与开发"},
    {"id": 3, "name": "大数据应用"},
    {"id": 4, "name": "云计算应用"},
    {"id": 5, "name": "企业数字化安全运维"},
    {"id": 6, "name": "工业互联网"},
    {"id": 7, "name": "人工智能应用"},
    {"id": 8, "name": "金融数据分析"},
]


class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    major = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "name": self.name,
            "major": self.major,
            "class": self.class_name
        }
    
    @staticmethod
    def create(student_id, name, major, class_name, password):
        from app import redis_client
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        student = Student(
            student_id=student_id,
            name=name,
            major=major,
            class_name=class_name,
            password_hash=password_hash
        )
        
        try:
            db.session.add(student)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    @staticmethod
    def get_by_id(student_id):
        return Student.query.filter_by(student_id=student_id).first()
    
    @staticmethod
    def verify_password(student_id, password):
        student = Student.get_by_id(student_id)
        if not student:
            return False
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return student.password_hash == password_hash
    
    @staticmethod
    def update_password(student_id, new_password):
        student = Student.get_by_id(student_id)
        if not student:
            return False
        student.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        db.session.commit()
        return True


class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(64), nullable=False)
    
    @staticmethod
    def init_admin():
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            admin = Admin(username='admin', password_hash=password_hash)
            db.session.add(admin)
            db.session.commit()
    
    @staticmethod
    def verify_password(username, password):
        admin = Admin.query.filter_by(username=username).first()
        if not admin:
            return False
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return admin.password_hash == password_hash


class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    max_capacity = db.Column(db.Integer, default=90)
    current_count = db.Column(db.Integer, default=0, index=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "max_capacity": self.max_capacity,
            "current_count": self.current_count
        }
    
    @staticmethod
    def init_courses():
        for course in COURSES:
            c = Course.query.filter_by(id=course["id"]).first()
            if not c:
                c = Course(
                    id=course["id"],
                    name=course["name"],
                    max_capacity=Config.MAX_COURSE_CAPACITY
                )
                db.session.add(c)
        db.session.commit()
    
    @staticmethod
    def get_all():
        return Course.query.all()
    
    @staticmethod
    def get_by_id(course_id):
        return Course.query.filter_by(id=course_id).first()
    
    @staticmethod
    def get_current_count(course_id):
        course = Course.query.filter_by(id=course_id).first()
        return course.current_count if course else 0
    
    @staticmethod
    def is_full(course_id):
        course = Course.query.filter_by(id=course_id).first()
        return course.current_count >= course.max_capacity if course else True
    
    @staticmethod
    def increment_count(course_id):
        course = Course.query.filter_by(id=course_id).first()
        if course and course.current_count < course.max_capacity:
            course.current_count += 1
            db.session.commit()
            return True
        return False


class Selection(db.Model):
    __tablename__ = 'selections'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), nullable=False, index=True)
    course_id = db.Column(db.Integer, nullable=False, index=True)
    selected_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_auto_assigned = db.Column(db.Boolean, default=False)
    confirmed = db.Column(db.Boolean, default=False)
    
    # 添加唯一约束，确保一个学生只能选一门课
    __table_args__ = (
        db.UniqueConstraint('student_id', name='uq_student_selection'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "selected_at": self.selected_at.isoformat() if self.selected_at else None,
            "is_auto_assigned": self.is_auto_assigned,
            "course_name": Course.get_by_id(self.course_id).name if self.course_id else None
        }
    
    @staticmethod
    def create(student_id, course_id):
        selection = Selection(
            student_id=student_id,
            course_id=course_id,
            confirmed=True
        )
        try:
            db.session.add(selection)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    @staticmethod
    def get_by_student(student_id):
        return Selection.query.filter_by(student_id=student_id).first()
    
    @staticmethod
    def has_selected(student_id):
        return Selection.query.filter_by(student_id=student_id).first() is not None


class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text, nullable=False)
    
    @staticmethod
    def get(key, default=None):
        config = SystemConfig.query.filter_by(key=key).first()
        return config.value if config else default
    
    @staticmethod
    def set(key, value):
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            config.value = value
        else:
            config = SystemConfig(key=key, value=value)
            db.session.add(config)
        db.session.commit()
    
    @staticmethod
    def get_selection_status():
        return SystemConfig.get('selection_status', 'not_started')
    
    @staticmethod
    def get_selection_start_time():
        return SystemConfig.get('selection_start_time', '')
    
    @staticmethod
    def init_config():
        configs = [
            ('selection_start_time', ''),
            ('selection_status', 'not_started'),
            ('selection_end_time', '')
        ]
        for key, value in configs:
            existing = SystemConfig.query.filter_by(key=key).first()
            if not existing:
                db.session.add(SystemConfig(key=key, value=value))
        db.session.commit()


def init_db():
    """初始化数据库"""
    db.create_all()
    Admin.init_admin()
    Course.init_courses()
    SystemConfig.init_config()


def drop_db():
    """删除所有表"""
    db.drop_all()
