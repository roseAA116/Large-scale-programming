import { FormEvent, useEffect, useState } from "react";
import { Save, UserRound } from "lucide-react";

import { ApiError, getCurrentUser, updateProfile } from "../api/client";
import { useAuthStore } from "../stores/authStore";

export function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const updateStoredUser = useAuthStore((state) => state.updateUser);
  const clearSession = useAuthStore((state) => state.clearSession);
  const [username, setUsername] = useState(user?.username ?? "");
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getCurrentUser()
      .then((freshUser) => {
        updateStoredUser(freshUser);
        setUsername(freshUser.username);
        setFullName(freshUser.full_name ?? "");
      })
      .catch(() => {
        clearSession();
      });
  }, [clearSession, updateStoredUser]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    setSubmitting(true);

    try {
      const updatedUser = await updateProfile({
        username,
        full_name: fullName
      });
      updateStoredUser(updatedUser);
      setMessage("个人资料已保存");
    } catch (caughtError) {
      const message =
        caughtError instanceof ApiError ? caughtError.message : "保存失败，请稍后重试";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">账号中心</p>
          <h2>个人资料</h2>
        </div>
      </header>

      <section className="profile-layout">
        <div className="profile-summary">
          <UserRound size={28} />
          <div>
            <h3>{user?.username}</h3>
            <p>{user?.email}</p>
          </div>
        </div>

        <form className="panel form profile-form" onSubmit={handleSubmit}>
          <div className="panel-header">
            <h3>资料编辑</h3>
            <code>/api/v1/users/me</code>
          </div>

          <div className="form-body">
            <label>
              邮箱
              <input value={user?.email ?? ""} disabled />
            </label>
            <label>
              用户名
              <input
                value={username}
                minLength={2}
                pattern="[A-Za-z0-9_\-]+"
                onChange={(event) => setUsername(event.target.value)}
                required
              />
            </label>
            <label>
              昵称
              <input value={fullName} onChange={(event) => setFullName(event.target.value)} />
            </label>

            {message && <p className="form-success">{message}</p>}
            {error && <p className="form-error">{error}</p>}

            <button className="primary-button" type="submit" disabled={submitting}>
              <Save size={18} />
              {submitting ? "保存中" : "保存资料"}
            </button>
          </div>
        </form>
      </section>
    </>
  );
}
