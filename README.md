# Large-scale-programming

课程学习助手 Agent 平台。

当前已完成阶段一基础骨架和阶段二用户与权限，源码放在本仓库内：

- 后端基础骨架：[backend](./backend)
- 前端基础骨架：[frontend](./frontend)
- 开发环境编排：[docker-compose.yml](./docker-compose.yml)
- 任务清单：[任务清单/course_agent_task_checklist.md](./任务清单/course_agent_task_checklist.md)

## 当前进度

已完成阶段一基础层：

- FastAPI 应用入口
- 统一 API 响应结构
- 全局错误处理与错误码结构
- trace_id 请求追踪
- 结构化日志
- 配置管理与环境变量示例
- PostgreSQL、Redis、MinIO 连接占位
- Alembic 迁移骨架
- Docker Compose 开发环境
- React + TypeScript + Vite 前端骨架

已完成阶段二用户与权限：

- 用户注册、登录、退出登录接口
- 密码哈希与密码校验
- JWT 签发、解析、过期校验和退出后失效
- 当前用户信息接口
- 个人资料查看与修改
- `users` 数据表和 Alembic 迁移
- 后续业务接口可复用的鉴权依赖和用户数据隔离校验
- 前端登录态管理、路由守卫、注册/登录页、个人资料页
- Docker Compose 容器内 PostgreSQL、Redis、MinIO、API、前端联调通过

## Docker 快速启动

```powershell
docker compose up -d --build
docker compose exec api alembic upgrade head
```

启动后可访问：

- 前端：`http://127.0.0.1:5173`
- API：`http://127.0.0.1:8000`
- API 文档：`http://127.0.0.1:8000/docs`
- MinIO 控制台：`http://127.0.0.1:9001`

详细启动方式见 [backend/README.md](./backend/README.md)。
