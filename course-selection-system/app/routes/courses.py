from flask import Blueprint, jsonify, render_template, session
from app.models import Course, SystemConfig, Selection
from datetime import datetime
import json

bp = Blueprint("courses", __name__, url_prefix="/courses")


@bp.route("/")
def course_list():
    if "user_id" not in session or session.get("is_admin"):
        return jsonify({"error": "未登录或无权访问"}), 401

    return render_template("courses.html")


@bp.route("/api/list")
def api_course_list():
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401

    courses = Course.get_all()
    student_id = session["user_id"]

    # 检查学生是否已选课
    selected = Selection.get_by_student(student_id)
    selected_course_id = selected["course_id"] if selected else None

    return jsonify({"courses": courses, "selected_course_id": selected_course_id})


@bp.route("/api/status")
def api_selection_status():
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401

    start_time_str = SystemConfig.get_selection_start_time()
    status = SystemConfig.get_selection_status()

    now = datetime.now()
    countdown = None
    selection_open = False

    if start_time_str:
        start_time = datetime.fromisoformat(start_time_str)
        if now < start_time:
            countdown = (start_time - now).total_seconds()
            selection_open = False
        else:
            # 检查是否在 30 分钟窗口内
            end_time = start_time.timestamp() + 30 * 60
            if now.timestamp() < end_time:
                countdown = end_time - now.timestamp()
                selection_open = True
            else:
                selection_open = False
                status = "ended"

    return jsonify(
        {
            "status": status,
            "selection_open": selection_open,
            "countdown": countdown,
            "start_time": start_time_str,
        }
    )
