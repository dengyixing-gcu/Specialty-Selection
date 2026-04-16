import pytest
import sys

sys.path.insert(0, "/home/xing/course-selection-system")

from app.models import Student, Course, Selection, SystemConfig, init_db, COURSES
import sqlite3
import os


@pytest.fixture
def db():
    # 使用测试数据库
    os.environ["DATABASE_URL"] = "sqlite:///test_course_selection.db"
    init_db()
    yield
    # 清理测试数据库
    if os.path.exists("instance/test_course_selection.db"):
        os.remove("instance/test_course_selection.db")


def test_student_create(db):
    result = Student.create(
        "202401010101", "张三", "计算机科学与技术", "1 班", "password123"
    )
    assert result is True

    student = Student.get_by_id("202401010101")
    assert student["name"] == "张三"
    assert student["major"] == "计算机科学与技术"


def test_student_duplicate(db):
    Student.create("202401010101", "张三", "计算机科学与技术", "1 班", "password123")
    result = Student.create("202401010101", "李四", "软件工程", "2 班", "password456")
    assert result is False


def test_student_verify_password(db):
    Student.create("202401010101", "张三", "计算机科学与技术", "1 班", "password123")
    assert Student.verify_password("202401010101", "password123") is True
    assert Student.verify_password("202401010101", "wrongpassword") is False


def test_course_initialization(db):
    courses = Course.get_all()
    assert len(courses) == 8

    for course in courses:
        assert course["max_capacity"] == 90
        assert course["current_count"] == 0


def test_selection_create(db):
    Student.create("202401010101", "张三", "计算机科学与技术", "1 班", "password123")
    Selection.create("202401010101", 1)

    selection = Selection.get_by_student("202401010101")
    assert selection is not None
    assert selection["course_id"] == 1


def test_auto_assignment_flag(db):
    Student.create("202401010101", "张三", "计算机科学与技术", "1 班", "password123")
    Selection.create("202401010101", 1, is_auto_assigned=True)

    selection = Selection.get_by_student("202401010101")
    assert selection["is_auto_assigned"] == 1


def test_system_config(db):
    SystemConfig.set_selection_start_time("2024-01-01T10:00:00")
    assert SystemConfig.get_selection_start_time() is not None

    SystemConfig.set_selection_status("open")
    assert SystemConfig.get_selection_status() == "open"
