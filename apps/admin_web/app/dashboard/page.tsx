'use client';

import { useEffect, useState } from "react";
import { DashboardShell } from "../components/DashboardShell";
import { fetchMe, fetchPermissions, fetchRoles, fetchUsers } from "../lib/api";
import type { Permission, Role, User } from "../lib/types";

export default function DashboardPage() {
  const [me, setMe] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [meData, usersData, rolesData, permissionsData] = await Promise.all([
          fetchMe(),
          fetchUsers(),
          fetchRoles(),
          fetchPermissions(),
        ]);
        setMe(meData);
        setUsers(usersData);
        setRoles(rolesData);
        setPermissions(permissionsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Load failed");
      }
    }
    load();
  }, []);

  return (
    <DashboardShell title="Дашборд" subtitle="Общая сводка рабочей платформы" currentUser={me}>
      {error ? <div className="panel error">{error}</div> : null}

      <div className="card-grid">
        <div className="metric-card">
          <div className="metric-label">Пользователи</div>
          <div className="metric-value">{users.length}</div>
          <div className="metric-sub">Активная команда проекта</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Роли</div>
          <div className="metric-value">{roles.length}</div>
          <div className="metric-sub">Текущая RBAC-схема</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Permissions</div>
          <div className="metric-value">{permissions.length}</div>
          <div className="metric-sub">Уже зарегистрировано в системе</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Текущий пользователь</div>
          <div className="metric-value">{me?.username ?? "..."}</div>
          <div className="metric-sub">{me?.is_superuser ? "Owner / Superuser" : "User"}</div>
        </div>
      </div>

      <div className="panel">
        <div className="table-title">Что уже реально готово</div>
        <div className="table-sub">
          API поднят на VPS, авторизация работает, Swagger доступен, роли и права читаются из БД.
        </div>
      </div>
    </DashboardShell>
  );
}
