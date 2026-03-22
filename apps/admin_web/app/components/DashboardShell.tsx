'use client';

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { User } from "../lib/types";

type Props = {
  title: string;
  subtitle: string;
  currentUser: User | null;
  children: React.ReactNode;
};

export function DashboardShell({ title, subtitle, currentUser, children }: Props) {
  const router = useRouter();

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    router.push("/login");
  }

  return (
    <div className="page-shell">
      <aside className="sidebar">
        <div className="brand">Anime<span>Platform</span></div>

        <div className="nav">
          <Link href="/dashboard">Дашборд</Link>
          <Link href="/users">Пользователи</Link>
          <Link href="/roles">Роли</Link>
          <Link href="/permissions">Permissions</Link>
          <button onClick={logout}>Выйти</button>
        </div>
      </aside>

      <main className="main">
        <div className="topbar">
          <div>
            <div className="table-title">{title}</div>
            <div className="table-sub">{subtitle}</div>
          </div>

          <div className="panel" style={{ padding: "12px 16px" }}>
            <div className="kv">
              <div>
                <b>Текущий пользователь:</b> {currentUser?.username ?? "..."}
              </div>
              <div>
                <b>Email:</b> {currentUser?.email ?? "..."}
              </div>
            </div>
          </div>
        </div>

        {children}
      </main>
    </div>
  );
}
