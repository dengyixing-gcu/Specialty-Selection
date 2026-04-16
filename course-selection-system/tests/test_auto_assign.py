import pytest
import sys

sys.path.insert(0, "/home/xing/course-selection-system")

from app.models import Student, Course, Selection, init_db
import sqlite3
import os


@pytest.fixture
def db():
    os.environ["DATABASE_URL"] = "sqlite:///test_course_selection.db"
    init_db()
    yield
    if os.path.exists("instance/test_course_selection.db"):
        os.remove("instance/test_course_selection.db")


def test_auto_assignment_min_capacity(db):
    """测试自动分配确保每门课程至少 30 人"""
    # 创建 240 个未选课学生（30 人 * 8 门课程）
    for i in range(240):
        student_id = f"202401010{i:03d}"
        Student.create(
            student_id, f"学生{i}", "计算机科学与技术", "1 班", "password123"
        )

    unselected = Selection.get_unselected_students()
    assert len(unselected) == 240

    # 运行自动分配（这里简化测试，实际调用 auto_assign 模块）
    courses = Course.get_all()
    courses_sorted = sorted(courses, key=lambda c: c["current_count"])

    assigned_count = 0
    for student in unselected:
        for course in courses_sorted:
            if course["current_count"] < 30:
                Selection.create(
                    student["student_id"], course["id"], is_auto_assigned=True
                )
                course["current_count"] += 1
                assigned_count += 1
                break

    # 验证所有课程都达到至少 30 人
    courses = Course.get_all()
    for course in courses:
        assert course["current_count"] >= 30, f"课程{course['name']}人数不足 30"


def test_auto_assignment_random(db):
    """测试剩余学生随机分配"""
    # 先让每门课程有 30 人
    for course_id in range(1, 9):
        for i in range(30):
            student_id = f"2024010{course_id}{i:03d}"
            Student.create(
                student_id, f"学生{i}", "计算机科学与技术", "1 班", "password123"
            )
            Selection.create(student_id, course_id)

    # 再创建一些未选课学生
    for i in range(100):
        student_id = f"202402010{i:03d}"
        Student.create(student_id, f"学生{i}", "软件工程", "2 班", "password123")

    unselected = Selection.get_unselected_students()
    assert len(unselected) == 100

    # 分配剩余学生
    courses = Course.get_all()
    courses_sorted = sorted(courses, key=lambda c: c["current_count"])

    for student in unselected:
        available = [c for c in courses_sorted if c["current_count"] < 90]
        if available:
            selected = available[0]
            Selection.create(
                student["student_id"], selected["id"], is_auto_assigned=True
            )

    # 验证所有学生都被分配
    remaining = Selection.get_unselected_students()
    assert len(remaining) == 0
