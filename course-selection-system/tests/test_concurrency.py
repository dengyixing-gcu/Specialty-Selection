"""
高并发选课压力测试脚本
模拟 800 名学生同时选课的场景
"""

import threading
import time
import random
import requests
from collections import defaultdict
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

# 测试结果
results = {
    "success": 0,
    "failed": 0,
    "full": 0,
    "error": 0,
    "total_time": 0,
    "details": []
}
results_lock = threading.Lock()

# 课程选择统计
course_stats = defaultdict(lambda: {"selected": 0, "failed": 0})


def create_student_session(student_id, password):
    """创建学生会话并登录"""
    session = requests.Session()
    
    login_data = {
        "student_id": student_id,
        "password": password
    }
    
    try:
        response = session.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            timeout=5
        )
        if response.status_code == 200:
            # 验证会话是否有效
            test_response = session.get(f"{BASE_URL}/courses/api/list", timeout=5)
            if test_response.status_code == 200:
                return session
        return None
    except Exception as e:
        print(f"创建会话失败 {student_id}: {e}")
        return None


def select_course(student_id, password, course_id):
    """选课操作 - 每个线程创建独立会话"""
    start_time = time.time()
    
    # 创建新会话并登录
    session = requests.Session()
    try:
        login_response = session.post(
            f"{BASE_URL}/auth/login",
            json={"student_id": student_id, "password": password},
            timeout=5
        )
        if login_response.status_code != 200:
            with results_lock:
                results["error"] += 1
            return
    except Exception:
        with results_lock:
            results["error"] += 1
        return
    
    try:
        response = session.post(
            f"{BASE_URL}/selection/select",
            json={"course_id": course_id},
            timeout=10
        )
        
        elapsed = time.time() - start_time
        
        with results_lock:
            if response.status_code == 200:
                results["success"] += 1
                course_stats[course_id]["selected"] += 1
                results["details"].append({
                    "student_id": student_id,
                    "course_id": course_id,
                    "status": "success",
                    "time": elapsed
                })
            elif response.status_code == 400:
                data = response.json()
                if "已满" in data.get("error", ""):
                    results["full"] += 1
                    course_stats[course_id]["failed"] += 1
                else:
                    results["failed"] += 1
                results["details"].append({
                    "student_id": student_id,
                    "course_id": course_id,
                    "status": "failed",
                    "error": data.get("error"),
                    "time": elapsed
                })
            else:
                results["error"] += 1
                results["details"].append({
                    "student_id": student_id,
                    "course_id": course_id,
                    "status": "error",
                    "http_status": response.status_code,
                    "time": elapsed
                })
                
    except Exception as e:
        elapsed = time.time() - start_time
        with results_lock:
            results["error"] += 1
            results["details"].append({
                "student_id": student_id,
                "course_id": course_id,
                "status": "exception",
                "error": str(e),
                "time": elapsed
            })


def run_concurrent_test(num_students=800, courses_per_student=1):
    """运行并发测试"""
    print(f"\n{'='*60}")
    print(f"高并发选课压力测试")
    print(f"{'='*60}")
    print(f"学生数量：{num_students}")
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 准备学生会话
    print("正在创建学生会话...")
    sessions = []
    student_ids = []
    
    for i in range(num_students):
        student_id = f"202600000{100+i:03d}"
        password = "test123"
        
        session = create_student_session(student_id, password)
        if session:
            sessions.append(session)
            student_ids.append(student_id)
        else:
            try:
                reg_response = requests.post(
                    f"{BASE_URL}/auth/register",
                    json={
                        "student_id": student_id,
                        "name": f"测试学生{i}",
                        "major": "数据科学与大数据技术",
                        "class": "1 班",
                        "password": password
                    },
                    timeout=5
                )
                if reg_response.status_code in [201, 400]:
                    session = create_student_session(student_id, password)
                    if session:
                        sessions.append(session)
                        student_ids.append(student_id)
            except Exception:
                pass
    
    print(f"成功创建 {len(sessions)} 个学生会话\n")
    
    if len(sessions) == 0:
        print("错误：无法创建任何学生会话")
        return
    
    course_assignments = [random.randint(1, 8) for _ in range(len(sessions))]
    
    print("开始并发选课...")
    start_time = time.time()
    
    threads = []
    for i, student_id in enumerate(student_ids):
        t = threading.Thread(
            target=select_course,
            args=(student_id, "test123", course_assignments[i])
        )
        threads.append(t)
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n{'='*60}")
    print(f"测试结果")
    print(f"{'='*60}")
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时：{total_time:.2f} 秒")
    print(f"成功：{results['success']}")
    print(f"失败（课程已满）：{results['full']}")
    print(f"失败（其他）：{results['failed']}")
    print(f"错误：{results['error']}")
    print(f"成功率：{results['success']/len(sessions)*100:.1f}%")
    print(f"\n课程统计:")
    for course_id in range(1, 9):
        stats = course_stats[course_id]
        print(f"  课程{course_id}: 成功{stats['selected']}, 失败{stats['failed']}")
    print(f"{'='*60}\n")
    
    return results


if __name__ == "__main__":
    print("正在开启选课...")
    admin_session = requests.Session()
    try:
        login_response = admin_session.post(
            f"{BASE_URL}/auth/login",
            json={"student_id": "admin", "password": "admin123", "is_admin": True},
            timeout=5
        )
        if login_response.status_code == 200:
            start_response = admin_session.post(
                f"{BASE_URL}/admin/api/start-selection",
                json={},
                timeout=5
            )
            print(f"选课状态：{'开启成功' if start_response.status_code == 200 else '开启失败'}")
    except Exception as e:
        print(f"开启选课失败：{e}")
    
    run_concurrent_test(num_students=800)
