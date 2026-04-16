from flask import Blueprint, jsonify
from app.models import Selection, Course, SystemConfig, MAJORS, CLASSES
import random

bp = Blueprint("auto_assign", __name__, url_prefix="/auto-assign")


@bp.route("/run", methods=["POST"])
def run_auto_assignment():
    """
    自动分配算法：
    1. 获取所有未选课学生
    2. 获取所有课程当前人数
    3. 优先分配至少 30 人到每门课程
    4. 剩余学生随机分配到未满课程
    """
    unselected = Selection.get_unselected_students()
    courses = Course.get_all()

    if not unselected:
        return jsonify({"message": "没有需要分配的学生", "assigned": 0}), 200

    # 按人数排序课程（优先填充人数少的）
    courses_sorted = sorted(courses, key=lambda c: c["current_count"])

    assigned_count = 0

    for student in unselected:
        # 找到第一个未满的课程
        assigned = False

        # 优先确保每门课程至少 30 人
        for course in courses_sorted:
            if course["current_count"] < 30:
                Selection.create(
                    student["student_id"], course["id"], is_auto_assigned=True
                )
                course["current_count"] += 1
                assigned_count += 1
                assigned = True
                break

        # 如果所有课程都达到 30 人，随机分配
        if not assigned:
            available_courses = [c for c in courses_sorted if c["current_count"] < 90]
            if available_courses:
                selected_course = random.choice(available_courses)
                Selection.create(
                    student["student_id"], selected_course["id"], is_auto_assigned=True
                )
                selected_course["current_count"] += 1
                assigned_count += 1

    return jsonify(
        {
            "message": f"自动分配完成",
            "assigned": assigned_count,
            "total": len(unselected),
        }
    ), 200
