# Course Agent Frontend

课程学习助手 Agent 平台前端，使用 React、TypeScript、Vite、React Router、TanStack Query、Zustand 和 lucide-react。

## 当前页面

- 注册页
- 登录页
- 工作台
- 课程管理页
- 个人资料页

## 当前能力

- 登录态本地持久化
- 受保护路由
- 统一 API 客户端
- 课程列表查询
- 课程关键词搜索
- 新增/编辑课程弹窗
- 删除课程确认
- 课程空状态展示
- 个人资料查看与修改

## 本地启动

```powershell
cd frontend
npm install
npm run dev
```

启动后访问：

- `http://127.0.0.1:5173`

默认会通过 Vite 代理访问后端：

- `/api` -> `http://127.0.0.1:8000`

如需修改代理目标，可设置：

```powershell
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8000"
npm run dev
```

## 代码检查

```powershell
npm run lint
npm run build
```
