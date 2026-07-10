import { BookOpen, FileText, LayoutDashboard, LogOut, UserRound } from "lucide-react";
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
          <NavLink className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`} to="/">
            <LayoutDashboard size={18} />
            工作台
          </NavLink>
          <NavLink
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
            to="/courses"
          >
            <BookOpen size={18} />
            课程
          </NavLink>
          <NavLink className="nav-item pending" to="/">
            <FileText size={18} />
            资料
          </NavLink>
          <NavLink
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
            to="/profile"
          >
            <UserRound size={18} />
            个人资料
          </NavLink>
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
