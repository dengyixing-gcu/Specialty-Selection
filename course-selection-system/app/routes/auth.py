from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from app.models import Student, Admin, MAJORS, CLASSES
import re

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", majors=MAJORS, classes=CLASSES)

    data = request.get_json()
    student_id = data.get("student_id", "")
    name = data.get("name", "")
    major = data.get("major", "")
    class_name = data.get("class", "")
    password = data.get("password", "")

    # 验证学号（12 位数字）
    if not re.match(r"^\d{12}$", student_id):
        return jsonify({"error": "学号必须为 12 位数字"}), 400

    # 验证专业
    if major not in MAJORS:
        return jsonify({"error": "专业选择无效"}), 400

    # 验证班级
    if class_name not in CLASSES:
        return jsonify({"error": "班级选择无效"}), 400

    # 验证姓名
    if not name or len(name) < 1:
        return jsonify({"error": "姓名不能为空"}), 400

    # 验证密码
    if not password or len(password) < 4:
        return jsonify({"error": "密码至少 4 位"}), 400

    # 创建学生账号
    if Student.create(student_id, name, major, class_name, password):
        return jsonify({"message": "注册成功"}), 201
    else:
        return jsonify({"error": "学号已存在"}), 400


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json()
    student_id = data.get("student_id", "")
    password = data.get("password", "")
    is_admin = data.get("is_admin", False)

    if is_admin:
        if Admin.verify_password(student_id, password):
            session["user_id"] = student_id
            session["is_admin"] = True
            return jsonify({"message": "登录成功", "redirect": "/admin"}), 200
        else:
            return jsonify({"error": "管理员账号或密码错误"}), 401
    else:
        if Student.verify_password(student_id, password):
            session["user_id"] = student_id
            session["is_admin"] = False
            return jsonify({"message": "登录成功", "redirect": "/courses"}), 200
        else:
            return jsonify({"error": "学号或密码错误"}), 401


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "已退出登录"}), 200


@bp.route("/change-password", methods=["POST"])
def change_password():
    if "user_id" not in session or session.get("is_admin"):
        return jsonify({"error": "未登录"}), 401

    data = request.get_json()
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")

    student_id = session["user_id"]

    # 验证原密码
    if not Student.verify_password(student_id, old_password):
        return jsonify({"error": "原密码错误"}), 400

    # 验证新密码
    if not new_password or len(new_password) < 4:
        return jsonify({"error": "新密码至少 4 位"}), 400

    # 验证确认密码
    if new_password != confirm_password:
        return jsonify({"error": "两次输入的密码不一致"}), 400

    # 更新密码
    Student.update_password(student_id, new_password)
    session.clear()
    return jsonify({"message": "密码修改成功，请重新登录"}), 200


@bp.route("/check-auth")
def check_auth():
    if "user_id" not in session:
        return jsonify({"authenticated": False}), 401

    return jsonify(
        {
            "authenticated": True,
            "user_id": session["user_id"],
            "is_admin": session.get("is_admin", False),
        }
    ), 200
