"""
800 学生并发选课压力测试
验证课程人数限制（90 人）是否正确生效
"""

import threading
import requests
import time
import random
import sqlite3
from datetime import datetime
from collections import defaultdict

BASE_URL = "http://127.0.0.1:5000"

# 测试结果
results = {
    "success": 0,
    "failed_full": 0,
    "failed_other": 0,
    "error": 0,
    "details": []
}
results_lock = threading.Lock()

# 课程统计
course_stats = defaultdict(lambda: {"success": 0, "full": 0})


def reset_database():
    """重置数据库"""
    print("[准备] 重置数据库...")
    conn = sqlite3.connect("instance/course_selection.db")
    conn.execute("UPDATE courses SET current_count = 0")
    conn.execute("DELETE FROM selections")
    conn.commit()
    conn.close()
    print("[准备] 数据库已重置\n")


def create_students(num_students=800):
    """批量创建学生账号"""
    print(f"[准备] 创建 {num_students} 个学生账号...")
    
    created = 0
    for i in range(num_students):
        student_id = f"20260000{i:04d}"  # 202600000000 - 202600000799
        try:
            response = requests.post(
                f"{BASE_URL}/auth/register",
                json={
                    "student_id": student_id,
                    "name": f"测试学生{i}",
                    "major": "数据科学与大数据技术",
                    "class": "1 班",
                    "password": "test123"
                },
                timeout=5
            )
            if response.status_code in [201, 400]:  # 400 表示已存在
                created += 1
        except Exception:
            pass
    
    print(f"[准备] 成功创建 {created} 个学生账号\n")
    return created


def enable_selection():
    """管理员开启选课"""
    print("[准备] 管理员开启选课...")
    session = requests.Session()
    
    try:
        session.post(
            f"{BASE_URL}/auth/login",
            json={"student_id": "admin", "password": "admin123", "is_admin": True},
            timeout=5
        )
        response = session.post(
            f"{BASE_URL}/admin/api/start-selection",
            json={},
            timeout=5
        )
        if response.status_code == 200:
            print("[准备] 选课已开启\n")
            return True
    except Exception as e:
        print(f"[准备] 开启选课失败：{e}\n")
    return False


def select_course(student_id, course_id):
    """学生选课"""
    session = requests.Session()
    start_time = time.time()
    
    try:
        # 登录
        login_response = session.post(
            f"{BASE_URL}/auth/login",
            json={"student_id": student_id, "password": "test123"},
            timeout=10
        )
        if login_response.status_code != 200:
            with results_lock:
                results["error"] += 1
            return
        
        # 选课
        select_response = session.post(
            f"{BASE_URL}/selection/select",
            json={"course_id": course_id},
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        with results_lock:
            if select_response.status_code == 200:
                results["success"] += 1
                course_stats[course_id]["success"] += 1
                results["details"].append({
                    "student_id": student_id,
                    "course_id": course_id,
                    "status": "success",
                    "time": elapsed
                })
            elif select_response.status_code == 400:
                data = select_response.json()
                if "已满" in data.get("error", ""):
                    results["failed_full"] += 1
                    course_stats[course_id]["full"] += 1
                    results["details"].append({
                        "student_id": student_id,
                        "course_id": course_id,
                        "status": "full",
                        "time": elapsed
                    })
                else:
                    results["failed_other"] += 1
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
                    "http_status": select_response.status_code,
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


def run_test(num_students=800, target_course_id=1):
    """运行并发测试"""
    print("=" * 70)
    print("800 学生并发选课压力测试")
    print("=" * 70)
    print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"学生数量：{num_students}")
    print(f"目标课程：{target_course_id}（容量限制：90 人）")
    print("=" * 70)
    
    # 准备阶段
    reset_database()
    create_students(num_students)
    if not enable_selection():
        print("测试中止：无法开启选课")
        return
    
    # 开始测试
    print(f"[测试] {num_students} 名学生同时选择课程 {target_course_id}...")
    print(f"[测试] 开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    threads = []
    
    # 创建所有线程
    for i in range(num_students):
        student_id = f"20260000{i:04d}"
        t = threading.Thread(target=select_course, args=(student_id, target_course_id))
        threads.append(t)
    
    # 同时启动所有线程
    for t in threads:
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    # 打印结果
    print(f"\n[完成] 结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[完成] 总耗时：{elapsed:.2f} 秒")
    print(f"[完成] 平均请求速率：{num_students/elapsed:.1f} 请求/秒\n")
    
    # 统计结果
    total = results["success"] + results["failed_full"] + results["failed_other"] + results["error"]
    print("=" * 70)
    print("测试结果统计")
    print("=" * 70)
    print(f"总请求数：{total}")
    print(f"选课成功：{results['success']}")
    print(f"失败（课程已满）：{results['failed_full']}")
    print(f"失败（其他原因）：{results['failed_other']}")
    print(f"系统错误：{results['error']}")
    print(f"成功率：{results['success']/total*100:.1f}%")
    
    # 验证课程人数
    print("\n" + "=" * 70)
    print("课程人数验证")
    print("=" * 70)
    
    conn = sqlite3.connect("instance/course_selection.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, current_count, max_capacity FROM courses WHERE id = ?", (target_course_id,))
    course = cursor.fetchone()
    conn.close()
    
    if course:
        print(f"课程 ID: {course['id']}")
        print(f"课程名称：{course['name']}")
        print(f"实际选课人数：{course['current_count']}")
        print(f"最大容量：{course['max_capacity']}")
        
        if course['current_count'] <= course['max_capacity']:
            print(f"\n[PASS] 验证通过：课程人数未超限 ({course['current_count']} <= {course['max_capacity']})")
        else:
            print(f"\n[FAIL] 验证失败：课程人数超限 ({course['current_count']} > {course['max_capacity']})")
    
    # 验证选课记录
    conn = sqlite3.connect("instance/course_selection.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM selections WHERE course_id = ?", (target_course_id,))
    selection_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n数据库选课记录数：{selection_count}")
    if selection_count == course['current_count']:
        print("[PASS] 数据一致性验证通过")
    else:
        print("[WARN] 数据一致性警告：选课记录数与实际人数不符")
    
    print("\n" + "=" * 70)
    print("测试结论")
    print("=" * 70)
    
    if course['current_count'] <= 90 and results['success'] == course['current_count']:
        print("[PASS] 并发控制测试通过！")
        print(f"   - 课程人数限制正确生效 ({course['current_count']}/90)")
        print(f"   - {results['failed_full']} 名学生因课程已满被正确拒绝")
        print(f"   - 无超卖现象")
    else:
        print("[FAIL] 并发控制测试失败！")
        print(f"   - 课程人数：{course['current_count']}/90")
        print(f"   - 可能存在并发问题")
    
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    run_test(num_students=800, target_course_id=1)
