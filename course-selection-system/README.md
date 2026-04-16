# 学生选课系统

一个简单的学生选课系统，支持 8 门课程，具备时间控制、人数限制和自动分配功能。

## 功能特性

### 学生功能
- 注册账号（学号、专业、班级、姓名、密码）
- 登录/退出
- 修改密码
- 查看课程列表和选课状态
- 选课（30 分钟窗口，确认后不可更改）
- 查看选课结果

### 管理员功能
- 设置选课开始时间
- 开始/结束选课
- 查看选课统计
- 修改学生信息
- 重置学生密码
- 导出选课结果（Excel）

## 技术栈

- 后端：Python + Flask
- 数据库：SQLite
- 缓存：Redis
- 前端：Bootstrap 5
- 部署：Docker

## 快速开始

### 本地开发

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 启动 Redis
```bash
redis-server
```

3. 初始化数据库并运行
```bash
python -c "from app.models import init_db; init_db()"
python run.py
```

4. 访问 http://localhost:5000

### Docker 部署

```bash
docker-compose up -d
```

访问 http://localhost:5000

## 默认账号

- 管理员：账号 `admin`，密码 `admin123`
- 学生：需要注册

## 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| MAX_COURSE_CAPACITY | 90 | 每门课程最大人数 |
| MIN_COURSE_CAPACITY | 30 | 每门课程最低人数 |
| COURSE_SELECTION_DURATION | 1800 | 选课时长（秒） |

## 高并发处理

系统采用以下策略应对高并发：

1. **Redis 分布式锁**：确保选课操作原子性
2. **SQLite WAL 模式**：支持并发读取
3. **请求限流**：防止系统过载
4. **缓存层**：减少数据库压力

## API 接口

### 认证
- POST `/auth/register` - 学生注册
- POST `/auth/login` - 登录
- POST `/auth/logout` - 退出
- POST `/auth/change-password` - 修改密码

### 课程
- GET `/courses/api/list` - 获取课程列表
- GET `/courses/api/status` - 获取选课状态

### 选课
- POST `/selection/select` - 选择课程
- GET `/selection/result` - 获取选课结果

### 管理员
- GET `/admin/api/status` - 获取选课状态
- POST `/admin/api/set-selection-time` - 设置选课时间
- POST `/admin/api/start-selection` - 开始选课
- POST `/admin/api/end-selection` - 结束选课
- GET `/admin/api/students` - 获取学生列表
- POST `/admin/api/student/update` - 更新学生信息
- POST `/admin/api/student/reset-password` - 重置密码
- GET `/admin/api/export` - 导出结果

### 自动分配
- POST `/auto-assign/run` - 运行自动分配

## 测试

```bash
# 单元测试
pytest tests/

# 并发测试
python tests/test_concurrency.py
```

## 课程列表

1. 企业数据资产管理
2. 企业数字化运营与开发
3. 大数据应用
4. 云计算应用
5. 企业数字化安全运维
6. 工业互联网
7. 人工智能应用
8. 金融数据分析
