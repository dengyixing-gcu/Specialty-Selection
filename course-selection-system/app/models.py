import sqlite3
import hashlib
import secrets
from datetime import datetime
from config import Config

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


def get_db_connection():
    conn = sqlite3.connect("instance/course_selection.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 学生表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            major TEXT NOT NULL,
            class TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 管理员表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # 课程表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            max_capacity INTEGER DEFAULT 90,
            current_count INTEGER DEFAULT 0
        )
    """)

    # 选课记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS selections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_auto_assigned BOOLEAN DEFAULT 0,
            confirmed BOOLEAN DEFAULT 0,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)

    # 系统配置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # 初始化课程数据
    for course in COURSES:
        cursor.execute(
            """
            INSERT OR IGNORE INTO courses (id, name, max_capacity, current_count)
            VALUES (?, ?, ?, 0)
        """,
            (course["id"], course["name"], Config.MAX_COURSE_CAPACITY),
        )

    # 初始化系统配置
    cursor.execute("""
        INSERT OR IGNORE INTO system_config (key, value)
        VALUES ('selection_start_time', ''),
               ('selection_status', 'not_started'),
               ('selection_end_time', '')
    """)

    # 创建默认管理员
    default_password = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute(
        """
        INSERT OR IGNORE INTO admins (username, password_hash)
        VALUES ('admin', ?)
    """,
        (default_password,),
    )

    conn.commit()
    conn.close()


class Student:
    @staticmethod
    def create(student_id, name, major, class_name, password):
        conn = get_db_connection()
        cursor = conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            cursor.execute(
                """
                INSERT INTO students (student_id, name, major, class, password_hash)
                VALUES (?, ?, ?, ?, ?)
            """,
                (student_id, name, major, class_name, password_hash),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def get_by_id(student_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def verify_password(student_id, password):
        student = Student.get_by_id(student_id)
        if not student:
            return False
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return student["password_hash"] == password_hash

    @staticmethod
    def update_password(student_id, new_password):
        conn = get_db_connection()
        cursor = conn.cursor()
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        cursor.execute(
            "UPDATE students SET password_hash = ? WHERE student_id = ?",
            (password_hash, student_id),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update_info(student_id, name=None, major=None, class_name=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        updates = []
        values = []
        if name:
            updates.append("name = ?")
            values.append(name)
        if major:
            updates.append("major = ?")
            values.append(major)
        if class_name:
            updates.append("class = ?")
            values.append(class_name)
        if updates:
            values.append(student_id)
            cursor.execute(
                f"UPDATE students SET {', '.join(updates)} WHERE student_id = ?", values
            )
            conn.commit()
        conn.close()

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


class Admin:
    @staticmethod
    def verify_password(username, password):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return False
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return row["password_hash"] == password_hash


class Course:
    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM courses")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_id(course_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_current_count(course_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT current_count FROM courses WHERE id = ?", (course_id,))
        row = cursor.fetchone()
        conn.close()
        return row["current_count"] if row else 0

    @staticmethod
    def increment_count(course_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE courses SET current_count = current_count + 1 WHERE id = ?",
            (course_id,),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def is_full(course_id):
        course = Course.get_by_id(course_id)
        if not course:
            return True
        return course["current_count"] >= course["max_capacity"]


class Selection:
    @staticmethod
    def create(student_id, course_id, is_auto_assigned=False):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO selections (student_id, course_id, is_auto_assigned, confirmed)
            VALUES (?, ?, ?, 1)
        """,
            (student_id, course_id, is_auto_assigned),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_student(student_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.*, c.name as course_name 
            FROM selections s 
            JOIN courses c ON s.course_id = c.id 
            WHERE s.student_id = ?
        """,
            (student_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def has_selected(student_id):
        return Selection.get_by_student(student_id) is not None

    @staticmethod
    def get_unselected_students():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM students 
            WHERE student_id NOT IN (SELECT student_id FROM selections)
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_all_with_info():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.student_id, s.name, s.major, s.class, 
                   c.name as course_name, sel.is_auto_assigned, sel.selected_at
            FROM students s
            LEFT JOIN selections sel ON s.student_id = sel.student_id
            LEFT JOIN courses c ON sel.course_id = c.id
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


class SystemConfig:
    @staticmethod
    def get(key):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_config WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row["value"] if row else None

    @staticmethod
    def set(key, value):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO system_config (key, value)
            VALUES (?, ?)
        """,
            (key, value),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_selection_start_time():
        value = SystemConfig.get("selection_start_time")
        if value:
            return datetime.fromisoformat(value)
        return None

    @staticmethod
    def set_selection_start_time(dt):
        SystemConfig.set("selection_start_time", dt.isoformat())

    @staticmethod
    def get_selection_status():
        return SystemConfig.get("selection_status") or "not_started"

    @staticmethod
    def set_selection_status(status):
        SystemConfig.set("selection_status", status)
