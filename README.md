# Large-scale-programming

课程学习助手 Agent 平台。

当前已开始搭建阶段一基础骨架，源码放在本仓库内：

- 后端基础骨架：[backend](./backend)
- 前端基础骨架：[frontend](./frontend)
- 开发环境编排：[docker-compose.yml](./docker-compose.yml)
- 任务清单：[任务清单/course_agent_task_checklist.md](./任务清单/course_agent_task_checklist.md)

## 当前进度

已完成 Python 后端基础层：

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

详细启动方式见 [backend/README.md](./backend/README.md)。
