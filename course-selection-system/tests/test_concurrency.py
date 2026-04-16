"""
并发测试脚本
测试选课系统在高并发场景下的表现
"""

import threading
import time
import sys

sys.path.insert(0, "/home/xing/course-selection-system")

from app.models import Student, Course, Selection, init_db
import requests
import os

BASE_URL = "http://localhost:5000"


def simulate_student_login(student_id, password):
    """模拟学生登录"""
    response = requests.post(
        f"{BASE_URL}/auth/login", json={"student_id": student_id, "password": password}
    )
    return response.cookies if response.ok else None


def simulate_course_selection(cookies, course_id):
    """模拟选课"""
    response = requests.post(
        f"{BASE_URL}/selection/select", json={"course_id": course_id}, cookies=cookies
    )
    return response.json()


def test_concurrent_selection():
    """测试并发选课"""
    print("开始并发选课测试...")

    # 准备测试数据
    os.environ["DATABASE_URL"] = "sqlite:///test_concurrency.db"
    init_db()

    # 创建 100 个学生
    for i in range(100):
        student_id = f"202401010{i:03d}"
        Student.create(
            student_id, f"学生{i}", "计算机科学与技术", "1 班", "password123"
        )

    results = {"success": 0, "failed": 0, "full": 0}
    lock = threading.Lock()

    def select_course(student_id):
        cookies = simulate_student_login(student_id, "password123")
        if not cookies:
            with lock:
                results["failed"] += 1
            return

        result = simulate_course_selection(cookies, 1)  # 都选课程 1

        with lock:
            if "选课成功" in str(result):
                results["success"] += 1
            elif "已满" in str(result):
                results["full"] += 1
            else:
                results["failed"] += 1

    # 并发执行
    threads = []
    start_time = time.time()

    for i in range(100):
        t = threading.Thread(target=select_course, args=(f"202401010{i:03d}",))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed = time.time() - start_time

    print(f"并发测试完成 (耗时：{elapsed:.2f}秒)")
    print(
        f"成功：{results['success']}, 课程已满：{results['full']}, 失败：{results['failed']}"
    )

    # 验证课程人数不超过 90
    course = Course.get_by_id(1)
    assert course["current_count"] <= 90, f"课程人数超限：{course['current_count']}"
    print(f"课程 1 最终人数：{course['current_count']}")


if __name__ == "__main__":
    test_concurrent_selection()
