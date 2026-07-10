# Large-scale-programming

课程学习助手 Agent 平台，面向大学生的多课程学习、资料管理、课程问答、学习计划和待办任务管理场景。

当前仓库包含：

- 后端服务：[backend](./backend)
- 前端应用：[frontend](./frontend)
- Docker Compose 开发环境：[docker-compose.yml](./docker-compose.yml)
- 实现任务清单：[任务清单/course_agent_task_checklist.md](./任务清单/course_agent_task_checklist.md)

## 当前进度

### 阶段一：项目基础骨架

已完成：

- FastAPI 后端应用入口
- React + TypeScript + Vite 前端骨架
- 统一 API 响应结构
- 全局错误处理和错误码结构
- `trace_id` 请求追踪
- 结构化日志
- 配置管理和环境变量加载
- PostgreSQL、Redis、MinIO 开发环境编排
- Alembic 数据库迁移骨架
- Docker Compose 开发环境

### 阶段二：用户与权限

已完成：

- 用户注册、登录、退出登录接口
- 密码哈希和密码校验
- JWT 签发、解析、过期校验和退出后失效
- 当前用户信息接口
- 个人资料查看与修改
- `users` 数据表和 Alembic 迁移
- 后续业务接口可复用的鉴权依赖
- 用户数据隔离校验入口
- 前端登录态管理、路由守卫、注册/登录页、个人资料页

### 阶段三：课程管理

已完成：

- `courses` 数据表和 Alembic 迁移
- 课程创建接口
- 课程列表接口
- 课程详情接口
- 课程编辑接口
- 课程软删除接口
- 课程关键词搜索
- 前端课程列表页
- 前端课程新增/编辑弹窗
- 前端删除确认
- 前端课程空状态展示

## 后端接口

认证与用户：

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`

课程管理：

- `POST /api/v1/courses`
- `GET /api/v1/courses`
- `GET /api/v1/courses?keyword=关键词`
- `GET /api/v1/courses/{course_id}`
- `PATCH /api/v1/courses/{course_id}`
- `DELETE /api/v1/courses/{course_id}`

健康检查：

- `GET /api/v1/healthz`
- `GET /api/v1/readyz`

## 数据库迁移

首次启动数据库后，需要执行：

```powershell
cd backend
alembic upgrade head
```

当前迁移包括：

- `202607100001_create_users.py`：创建 `users` 表
- `202607100002_create_courses.py`：创建 `courses` 表

说明：`courses.deleted_at` 用于软删除。课程列表、详情、编辑和删除接口只处理当前登录用户自己的未删除课程。

## Docker 快速启动

在项目根目录运行：

```powershell
docker compose up -d --build
docker compose exec api alembic upgrade head
```

启动后可访问：

- 前端：`http://127.0.0.1:5173`
- API：`http://127.0.0.1:8000`
- API 文档：`http://127.0.0.1:8000/docs`
- MinIO 控制台：`http://127.0.0.1:9001`

## 本地开发

后端：

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

## 代码检查

后端：

```powershell
cd backend
python -m compileall app
python -m ruff check app tests
pytest
```

前端：

```powershell
cd frontend
npm run lint
npm run build
```

## 最近验证

阶段三完成后已通过：

- `python -m compileall app`
- `python -m ruff check app tests`
- `pytest`
- `npm run lint`
- `npm run build`
