from flask import Blueprint, request, jsonify, render_template, session, send_file
from app.models import Student, Course, Selection, SystemConfig
from datetime import datetime
import io
from openpyxl import Workbook

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
def admin_dashboard():
    if "user_id" not in session or not session.get("is_admin"):
        return jsonify({"error": "未授权"}), 401

    return render_template("admin.html")


@bp.route("/api/status")
def api_status():
    if "user_id" not in session or not session.get("is_admin"):
        return jsonify({"error": "未授权"}), 401

    start_time = SystemConfig.get_selection_start_time()
    status = SystemConfig.get_selection_status()

    courses = Course.get_all()
    total_students = len(Student.get_all())
    selected_count = len(Selection.get_all_with_info())

    return jsonify(
        {
            "status": status,
            "start_time": start_time,
            "total_students": total_students,
            "selected_count": selected_count,
            "courses": courses,
        }
    )


@bp.route("/api/set-selection-time", methods=["POST"])
def set_selection_time():
    if "user_id" not in session or not session.get("is_admin"):
        return jsonify({"error": "未授权"}), 401

    data = request.get_json()
    start_time_str = data.get("start_time")

    if not start_time_str:
        return jsonify({"error": "请选择开始时间"}), 400

    start_time = datetime.fromisoformat(start_time_str)
    now = datetime.now()

    if start_time <= now:
        return jsonify({"error": "选课开始时间不能早于当前时间"}), 400

    SystemConfig.set_selection_start_time(start_time)
    SystemConfig.set_selection_status("scheduled")

    return jsonify({"message": "选课时间设置成功", "start_time": start_time_str}), 200


@bp.route("/api/students")
def get_students():
    if "user_id" not in session or not session.get("is_admin"):
        return jsonify({"error": "未授权"}), 401

    students = Student.get_all()
    return jsonify({"students": students})


@bp.route("/api/student/update", methods=["POST"])
def update_student():
    if "user_id" not in session or not session.get("is_admin"):
        return jsonify({"error": "未授权"}), 401

    data = request.get_json()
    student_id = data.get("student_id")
    name = data.get("name")
    major = data.get("major")
    class_name = data.get("class")

    if not student_id:
        return jsonify({"error": "学号无效"}), 400

    Student.update_info(student_id, name, major, class_name)
    return jsonify({"message": "学生信息更新成功"}), 200


@bp.route("/api/student/reset-password", methods=["POST"])
def reset_password():
    if "user_id" not in session or not session.get("is_admin"):
        return jsonify({"error": "未授权"}), 401

    data = request.get_json()
    student_id = data.get("student_id")

    if not student_id:
        return jsonify({"error": "学号无效"}), 400

    # 重置为默认密码
    default_password = "123456"
    Student.update_password(student_id, default_password)

    return jsonify({"message": "密码已重置", "new_password": default_password}), 200


@bp.route("/api/export", methods=["GET"])
def export_results():
    if "user_id" not in session or not session.get("is_admin"):
        return jsonify({"error": "未授权"}), 401

    selections = Selection.get_all_with_info()

    wb = Workbook()
    ws = wb.active
    ws.title = "选课结果"

    # 表头
    ws.append(["学号", "姓名", "专业", "班级", "课程名称", "分配方式", "选课时间"])

    # 数据
    for sel in selections:
        assignment_type = "系统分配" if sel.get("is_auto_assigned") else "自主选择"
        ws.append(
            [
                sel.get("student_id"),
                sel.get("name"),
                sel.get("major"),
                sel.get("class"),
                sel.get("course_name") or "未选课",
                assignment_type,
                sel.get("selected_at") or "",
            ]
        )

    # 保存到内存
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"选课结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
    )


@bp.route("/api/start-selection", methods=["POST"])
def start_selection():
    if "user_id" not in session or not session.get("is_admin"):
        return jsonify({"error": "未授权"}), 401

    SystemConfig.set_selection_status("open")
    return jsonify({"message": "选课已开始"}), 200


@bp.route("/api/end-selection", methods=["POST"])
def end_selection():
    if "user_id" not in session or not session.get("is_admin"):
        return jsonify({"error": "未授权"}), 401

    SystemConfig.set_selection_status("ended")
    return jsonify({"message": "选课已结束"}), 200
