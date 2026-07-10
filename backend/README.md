# Course Agent Backend

课程学习助手 Agent 平台后端，使用 FastAPI、SQLAlchemy、Alembic、PostgreSQL、Redis 和 MinIO。

## 当前能力

- 统一 API 响应结构
- 全局错误处理
- `trace_id` 请求追踪
- JSON 结构化日志
- Pydantic 配置管理
- PostgreSQL / Redis / MinIO 开发环境配置
- Alembic 数据库迁移
- 健康检查接口
- 用户注册、登录、退出登录
- 密码哈希和密码校验
- JWT 签发、解析、过期校验和退出后失效
- 当前用户信息接口
- 个人资料查看与修改
- 用户数据隔离校验辅助函数
- 课程创建、列表、详情、编辑、软删除和关键词搜索

## 本地启动

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

启动后可访问：

- `http://127.0.0.1:8000/api/v1/healthz`
- `http://127.0.0.1:8000/api/v1/readyz`
- `http://127.0.0.1:8000/docs`

## 数据库迁移

```powershell
alembic upgrade head
```

当前迁移：

- `202607100001_create_users.py`
- `202607100002_create_courses.py`

`courses` 表字段：

- `id`
- `user_id`
- `name`
- `description`
- `teacher`
- `semester`
- `created_at`
- `updated_at`
- `deleted_at`

## 接口列表

认证与用户：

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`

课程：

- `POST /api/v1/courses`
- `GET /api/v1/courses`
- `GET /api/v1/courses?keyword=关键词`
- `GET /api/v1/courses/{course_id}`
- `PATCH /api/v1/courses/{course_id}`
- `DELETE /api/v1/courses/{course_id}`

## Docker Compose

在项目根目录运行：

```powershell
docker compose up -d --build
docker compose exec api alembic upgrade head
```

服务端口：

- API：`http://127.0.0.1:8000`
- PostgreSQL：`localhost:5432`
- Redis：`localhost:6379`
- MinIO API：`http://127.0.0.1:9000`
- MinIO Console：`http://127.0.0.1:9001`

## 代码检查

```powershell
python -m compileall app
python -m ruff check app tests
pytest
```

## 目录说明

```text
backend/
  app/
    api/        HTTP 路由
    core/       配置、日志、响应、错误和中间件
    db/         数据库连接与 ORM 基类
    models/     SQLAlchemy 模型
    schemas/    请求/响应结构
    services/   缓存、对象存储等服务封装
  migrations/   Alembic 迁移目录
  tests/        基础测试
```
