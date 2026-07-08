import { Activity, BookOpen, CheckCircle2, Database, FileText, Server } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getHealth } from "./api/client";

const modules = [
  { title: "课程管理", description: "课程列表、课程详情和课程资料将接在这里。", icon: BookOpen },
  { title: "资料索引", description: "上传、解析、分块和向量索引将接入后端任务。", icon: FileText },
  { title: "Agent 问答", description: "课程内检索、来源引用和对话记录会形成核心闭环。", icon: Activity }
];

export function App() {
  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: 1
  });

  const apiOnline = healthQuery.data?.success === true;

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">课</div>
          <div>
            <h1>课程学习助手</h1>
            <p>Agent Platform</p>
          </div>
        </div>

        <nav className="nav-list" aria-label="主导航">
          <a className="nav-item active" href="/">
            <Server size={18} />
            工作台
          </a>
          <a className="nav-item" href="/">
            <BookOpen size={18} />
            课程
          </a>
          <a className="nav-item" href="/">
            <FileText size={18} />
            资料
          </a>
        </nav>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">阶段一基础骨架</p>
            <h2>本地开发工作台</h2>
          </div>
          <div className={apiOnline ? "status online" : "status offline"}>
            <span />
            {apiOnline ? "API 在线" : "API 未连接"}
          </div>
        </header>

        <section className="overview">
          <div className="metric">
            <Database size={20} />
            <div>
              <strong>PostgreSQL + pgvector</strong>
              <span>数据库连接已预留</span>
            </div>
          </div>
          <div className="metric">
            <Server size={20} />
            <div>
              <strong>FastAPI</strong>
              <span>统一响应与健康检查已就绪</span>
            </div>
          </div>
          <div className="metric">
            <CheckCircle2 size={20} />
            <div>
              <strong>Trace ID</strong>
              <span>请求追踪和结构化日志已接入</span>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h3>后端健康检查</h3>
            <code>/api/v1/healthz</code>
          </div>
          <pre>{JSON.stringify(healthQuery.data ?? { status: "waiting" }, null, 2)}</pre>
        </section>

        <section className="module-grid">
          {modules.map((item) => {
            const Icon = item.icon;
            return (
              <article className="module-card" key={item.title}>
                <Icon size={22} />
                <h3>{item.title}</h3>
                <p>{item.description}</p>
              </article>
            );
          })}
        </section>
      </section>
    </main>
  );
}

