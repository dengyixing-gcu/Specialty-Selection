from flask import Blueprint, request, jsonify, session
from app.models import Selection, Course, SystemConfig
from concurrency import rate_limit, atomic_select_course

bp = Blueprint("selection", __name__, url_prefix="/selection")


@bp.route("/select", methods=["POST"])
@rate_limit
def select_course():
    if "user_id" not in session or session.get("is_admin"):
        return jsonify({"error": "未登录或无权访问"}), 401

    student_id = session["user_id"]
    data = request.get_json()
    course_id = data.get("course_id")

    if not course_id:
        return jsonify({"error": "课程 ID 无效"}), 400

    # 检查是否已选课
    if Selection.has_selected(student_id):
        return jsonify({"error": "您已选择课程，不可更改"}), 400

    # 检查选课时间
    status = SystemConfig.get_selection_status()
    if status != "open":
        return jsonify({"error": "选课时间未到或已结束"}), 400

    # 检查课程是否已满（快速检查）
    if Course.is_full(course_id):
        return jsonify({"error": "课程已满"}), 400

    # 原子性选课操作（使用 Redis 分布式锁或数据库锁）
    success, message = atomic_select_course(student_id, course_id)
    
    if success:
        return jsonify({"message": message, "course_id": course_id}), 200
    else:
        return jsonify({"error": message}), 400


@bp.route("/result")
def selection_result():
    if "user_id" not in session or session.get("is_admin"):
        return jsonify({"error": "未登录或无权访问"}), 401

    student_id = session["user_id"]
    selection = Selection.get_by_student(student_id)

    if selection:
        return jsonify(
            {
                "has_selected": True,
                "course_id": selection.course_id,
                "course_name": selection.course_name,
                "is_auto_assigned": bool(selection.is_auto_assigned),
                "selected_at": selection.selected_at.isoformat() if selection.selected_at else None,
            }
        )
    else:
        return jsonify({"has_selected": False}), 200


@bp.route("/queue-status")
def queue_status():
    """获取选课队列状态"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401

    student_id = session["user_id"]
    # 队列功能保留，当前主要使用锁机制
    
    return jsonify({
        "queue_size": 0,
        "your_position": None,
        "in_queue": False
    })
