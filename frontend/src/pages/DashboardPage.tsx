import { Activity, CalendarDays, CheckCircle2, ClipboardList, Database, MessageSquare } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getDashboardSummary, getHealth } from "../api/client";
import { useAuthStore } from "../stores/authStore";

export function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const healthQuery = useQuery({ queryKey: ["health"], queryFn: getHealth, retry: 1 });
  const dashboardQuery = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: getDashboardSummary,
    retry: 1
  });
  const summary = dashboardQuery.data;
  const apiOnline = healthQuery.data?.success === true;

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">个人中心与仪表盘</p>
          <h2>你好，{user?.full_name || user?.username}</h2>
        </div>
        <div className={apiOnline ? "status online" : "status offline"}>
          <span />
          {apiOnline ? "API 在线" : "API 未连接"}
        </div>
      </header>

      <section className="overview">
        <Metric icon={Database} label="课程" value={summary?.course_count ?? 0} />
        <Metric icon={Activity} label="资料 READY" value={`${Math.round((summary?.ready_material_ratio ?? 0) * 100)}%`} />
        <Metric icon={CheckCircle2} label="今日待办" value={summary?.today_tasks.length ?? 0} />
      </section>

      <section className="dashboard-grid">
        <article className="panel dashboard-panel">
          <div className="panel-header">
            <h3>今日任务</h3>
            <Link className="text-link" to="/tasks">查看待办</Link>
          </div>
          <div className="dashboard-list">
            {(summary?.today_tasks ?? []).length === 0 ? (
              <p className="materials-hint">今天还没有待办任务。</p>
            ) : (
              summary?.today_tasks.map((task) => (
                <div className="dashboard-list-item" key={task.id}>
                  <ClipboardList size={17} />
                  <span>{task.title}</span>
                </div>
              ))
            )}
          </div>
        </article>

        <article className="panel dashboard-panel">
          <div className="panel-header">
            <h3>最近对话</h3>
            <Link className="text-link" to="/chat">继续对话</Link>
          </div>
          <div className="dashboard-list">
            {(summary?.recent_chats ?? []).length === 0 ? (
              <p className="materials-hint">还没有课程问答记录。</p>
            ) : (
              summary?.recent_chats.map((chat) => (
                <div className="dashboard-list-item" key={chat.id}>
                  <MessageSquare size={17} />
                  <span>{chat.title}</span>
                </div>
              ))
            )}
          </div>
        </article>

        <article className="panel dashboard-panel">
          <div className="panel-header">
            <h3>近期计划</h3>
            <Link className="text-link" to="/plans">打开学习计划</Link>
          </div>
          <div className="dashboard-list">
            {(summary?.recent_plans ?? []).length === 0 ? (
              <p className="materials-hint">还没有学习计划。</p>
            ) : (
              summary?.recent_plans.map((plan) => (
                <div className="dashboard-list-item" key={plan.id}>
                  <CalendarDays size={17} />
                  <span>{plan.goal}</span>
                </div>
              ))
            )}
          </div>
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
  icon: typeof Database;
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
