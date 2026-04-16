from flask import Blueprint, request, jsonify, session
from app.models import Selection, Course, SystemConfig
from app import get_redis
import time

bp = Blueprint("selection", __name__, url_prefix="/selection")


@bp.route("/select", methods=["POST"])
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

    # 检查课程是否已满
    if Course.is_full(course_id):
        return jsonify({"error": "课程已满"}), 400

    # 使用 Redis 锁确保原子操作
    redis = get_redis()
    lock_key = f"course_lock:{course_id}"
    lock_acquired = redis.set(lock_key, "1", nx=True, ex=5)

    if not lock_acquired:
        return jsonify({"error": "系统繁忙，请稍后重试"}), 503

    try:
        # 再次检查课程人数（防止并发）
        current_count = Course.get_current_count(course_id)
        if current_count >= 90:
            return jsonify({"error": "课程已满"}), 400

        # 创建选课记录
        Selection.create(student_id, course_id)

        # 更新课程人数
        Course.increment_count(course_id)

        # 更新 Redis 缓存
        redis.set(f"course_count:{course_id}", current_count + 1)

        return jsonify({"message": "选课成功", "course_id": course_id}), 200

    finally:
        redis.delete(lock_key)


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
                "course_id": selection["course_id"],
                "course_name": selection["course_name"],
                "is_auto_assigned": bool(selection["is_auto_assigned"]),
                "selected_at": selection["selected_at"],
            }
        )
    else:
        return jsonify({"has_selected": False}), 200
