import {
  BookOpen,
  CalendarDays,
  ClipboardList,
  FileText,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  Settings,
  Sparkles,
  UserRound
} from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { logout } from "../api/client";
import { useAuthStore } from "../stores/authStore";

export function AppLayout() {
  const user = useAuthStore((state) => state.user);
  const clearSession = useAuthStore((state) => state.clearSession);
  const navigate = useNavigate();

  async function handleLogout() {
    try {
      await logout();
    } finally {
      clearSession();
      navigate("/login", { replace: true });
    }
  }

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
          <NavItem to="/" icon={LayoutDashboard} label="工作台" />
          <NavItem to="/courses" icon={BookOpen} label="课程" />
          <NavLink className="nav-item pending" to="/courses">
            <FileText size={18} />
            资料
          </NavLink>
          <NavItem to="/chat" icon={MessageSquare} label="问答" />
          <NavItem to="/summaries" icon={Sparkles} label="知识点" />
          <NavItem to="/plans" icon={CalendarDays} label="计划" />
          <NavItem to="/tasks" icon={ClipboardList} label="待办" />
          <NavItem to="/admin" icon={Settings} label="运维" />
          <NavItem to="/profile" icon={UserRound} label="个人资料" />
        </nav>

        <div className="sidebar-footer">
          <div>
            <strong>{user?.username ?? "未登录"}</strong>
            <span>{user?.email}</span>
          </div>
          <button className="icon-button" type="button" onClick={handleLogout} aria-label="退出登录">
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      <section className="content">
        <Outlet />
      </section>
    </main>
  );
}

function NavItem({
  icon: Icon,
  label,
  to
}: {
  icon: typeof LayoutDashboard;
  label: string;
  to: string;
}) {
  return (
    <NavLink className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`} to={to}>
      <Icon size={18} />
      {label}
    </NavLink>
  );
}
