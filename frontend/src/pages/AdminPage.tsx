import { Database, Server, ShieldCheck } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getAdminQueueStatus, getAdminStatus, getReadyz } from "../api/client";
import { useAuthStore } from "../stores/authStore";

export function AdminPage() {
  const user = useAuthStore((state) => state.user);
  const statusQuery = useQuery({ queryKey: ["admin-status"], queryFn: getAdminStatus, retry: 1 });
  const queueQuery = useQuery({ queryKey: ["admin-queues"], queryFn: getAdminQueueStatus, retry: 1 });
  const readyQuery = useQuery({ queryKey: ["readyz"], queryFn: getReadyz, retry: 1 });

  if (!user?.is_admin) {
    return (
      <section className="panel empty-state">
        <ShieldCheck size={34} />
        <h3>需要管理员权限</h3>
        <p>当前账号不是管理员，无法查看运维面板。</p>
      </section>
    );
  }

  const status = statusQuery.data;
  const queue = queueQuery.data;

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">管理员与运维</p>
          <h2>系统状态</h2>
        </div>
      </header>
      <section className="overview">
        <Metric icon={ShieldCheck} label="用户" value={status?.users ?? 0} />
        <Metric icon={Database} label="资料" value={status?.materials ?? 0} />
        <Metric icon={Server} label="失败资料" value={status?.failed_materials ?? 0} />
      </section>
      <section className="dashboard-grid">
        <article className="panel">
          <div className="panel-header"><h3>依赖检查</h3><code>/readyz</code></div>
          <pre>{JSON.stringify(readyQuery.data ?? { status: "loading" }, null, 2)}</pre>
        </article>
        <article className="panel">
          <div className="panel-header"><h3>异步队列</h3><code>{queue?.queue_name ?? "queue"}</code></div>
          <pre>{JSON.stringify(queue ?? { status: "loading" }, null, 2)}</pre>
        </article>
      </section>
    </>
  );
}

function Metric({
  icon: Icon,
  label,
  value
}: {
  icon: typeof ShieldCheck;
  label: string;
  value: number | string;
}) {
  return (
    <div className="metric">
      <Icon size={20} />
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}
