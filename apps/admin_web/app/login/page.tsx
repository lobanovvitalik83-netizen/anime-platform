'use client';

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "../../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [emailOrUsername, setEmailOrUsername] = useState("owner");
  const [password, setPassword] = useState("ChangeThisOwnerPassword123!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const tokens = await login(emailOrUsername, password);
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-title">Anime Platform</div>
        <div className="login-subtitle">Вход в рабочую панель управления</div>

        <form onSubmit={onSubmit} className="form-grid">
          <label>
            Логин или email
            <input
              value={emailOrUsername}
              onChange={(e) => setEmailOrUsername(e.target.value)}
              placeholder="owner"
            />
          </label>

          <label>
            Пароль
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Введите пароль"
            />
          </label>

          {error ? <div className="error">{error}</div> : null}

          <button className="primary" type="submit" disabled={loading}>
            {loading ? "Вход..." : "Войти"}
          </button>
        </form>

        <div style={{ height: 18 }} />

        <div className="helper">
          Эта панель уже подключена к твоему API. После входа доступны пользователи, роли,
          права и сводка системы.
        </div>
      </div>
    </div>
  );
}
