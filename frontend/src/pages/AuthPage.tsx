import { FormEvent, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { LogIn, UserPlus } from "lucide-react";

import { ApiError, login, register } from "../api/client";
import { useAuthStore } from "../stores/authStore";

type AuthPageProps = {
  mode: "login" | "register";
};

type LocationState = {
  from?: {
    pathname?: string;
  };
};

export function AuthPage({ mode }: AuthPageProps) {
  const isRegister = mode === "register";
  const setSession = useAuthStore((state) => state.setSession);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState | null;
  const redirectTo = state?.from?.pathname ?? "/";

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const session = isRegister
        ? await register({
            email,
            username,
            password,
            full_name: fullName || undefined
          })
        : await login({ email, password });
      setSession(session);
      navigate(redirectTo, { replace: true });
    } catch (caughtError) {
      const message =
        caughtError instanceof ApiError ? caughtError.message : "请求失败，请稍后重试";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  const Icon = isRegister ? UserPlus : LogIn;

  return (
    <main className="auth-screen">
      <section className="auth-panel" aria-labelledby="auth-title">
        <div className="auth-brand">
          <div className="brand-mark">课</div>
          <div>
            <p className="eyebrow">课程学习助手</p>
            <h1 id="auth-title">{isRegister ? "创建账号" : "登录账号"}</h1>
          </div>
        </div>

        <form className="form" onSubmit={handleSubmit}>
          <label>
            邮箱
            <input
              autoComplete="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          {isRegister && (
            <>
              <label>
                用户名
                <input
                  autoComplete="username"
                  value={username}
                  minLength={2}
                  pattern="[A-Za-z0-9_\-]+"
                  onChange={(event) => setUsername(event.target.value)}
                  required
                />
              </label>
              <label>
                昵称
                <input
                  autoComplete="name"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                />
              </label>
            </>
          )}

          <label>
            密码
            <input
              autoComplete={isRegister ? "new-password" : "current-password"}
              type="password"
              minLength={isRegister ? 8 : 1}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {error && <p className="form-error">{error}</p>}

          <button className="primary-button" type="submit" disabled={submitting}>
            <Icon size={18} />
            {submitting ? "处理中" : isRegister ? "注册并进入" : "登录"}
          </button>
        </form>

        <p className="auth-switch">
          {isRegister ? "已有账号？" : "还没有账号？"}
          <Link to={isRegister ? "/login" : "/register"}>
            {isRegister ? "去登录" : "去注册"}
          </Link>
        </p>
      </section>
    </main>
  );
}
