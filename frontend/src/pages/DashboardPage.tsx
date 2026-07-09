import { Activity, CheckCircle2, Database, FileText, ShieldCheck } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getHealth } from "../api/client";
import { useAuthStore } from "../stores/authStore";

const modules = [
  { title: "用户注册与登录", description: "邮箱、用户名、密码哈希和 JWT 登录已接入。", icon: ShieldCheck },
  { title: "资料索引", description: "后续上传、解析、分块和向量索引会在鉴权后接入。", icon: FileText },
  { title: "Agent 问答", description: "课程内检索、来源引用和对话记录会形成核心闭环。", icon: Activity }
];

export function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: 1
  });

  const apiOnline = healthQuery.data?.success === true;

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">阶段二用户与权限</p>
          <h2>你好，{user?.full_name || user?.username}</h2>
        </div>
        <div className={apiOnline ? "status online" : "status offline"}>
          <span />
          {apiOnline ? "API 在线" : "API 未连接"}
        </div>
      </header>

      <section className="overview">
        <div className="metric">
          <ShieldCheck size={20} />
          <div>
            <strong>JWT 鉴权</strong>
            <span>受保护接口自动携带登录凭证</span>
          </div>
        </div>
        <div className="metric">
          <Database size={20} />
          <div>
            <strong>用户数据隔离</strong>
            <span>后端已提供 owner 校验入口</span>
          </div>
        </div>
        <div className="metric">
          <CheckCircle2 size={20} />
          <div>
            <strong>退出失效</strong>
            <span>退出后旧 token 立即不可用</span>
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
    </>
  );
}
