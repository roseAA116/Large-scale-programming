# Course Agent Backend

这是课程学习助手 Agent 平台的 Python 后端基础骨架，当前覆盖阶段一的后端地基：

- FastAPI 应用入口
- 统一 API 响应结构
- 全局错误处理
- trace_id 请求追踪
- JSON 结构化日志
- Pydantic 配置管理
- PostgreSQL / Redis / MinIO 连接占位
- Alembic 数据库迁移骨架
- 健康检查接口

## 本地启动

建议先创建虚拟环境：

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
copy .env.example .env
uvicorn app.main:app --reload
```

启动后可访问：

- `http://127.0.0.1:8000/api/v1/healthz`
- `http://127.0.0.1:8000/api/v1/readyz`
- `http://127.0.0.1:8000/docs`

## Docker Compose

在项目根目录运行：

```powershell
docker compose up --build
```

服务端口：

- API: `http://127.0.0.1:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- MinIO API: `http://127.0.0.1:9000`
- MinIO Console: `http://127.0.0.1:9001`

## 目录说明

```text
backend/
  app/
    api/        HTTP 路由
    core/       配置、日志、响应、错误、中间件
    db/         数据库连接与 ORM 基类
    models/     后续业务模型
    schemas/    后续请求/响应结构
    services/   缓存、对象存储等服务封装
  migrations/   Alembic 迁移目录
  tests/        基础测试
```

