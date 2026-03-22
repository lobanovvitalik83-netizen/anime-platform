'use client';

import { useEffect, useState } from "react";
import { DashboardShell } from "../components/DashboardShell";
import { fetchMe, fetchUsers } from "../lib/api";
import type { User } from "../lib/types";

export default function UsersPage() {
  const [me, setMe] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    async function load() {
      const [meData, usersData] = await Promise.all([fetchMe(), fetchUsers()]);
      setMe(meData);
      setUsers(usersData);
    }
    load();
  }, []);

  return (
    <DashboardShell title="Пользователи" subtitle="Список сотрудников системы" currentUser={me}>
      <div className="table-wrap">
        <div className="table-toolbar">
          <div>
            <div className="table-title">Пользователи</div>
            <div className="table-sub">Данные приходят из /api/v1/users</div>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Логин</th>
              <th>Email</th>
              <th>Статус</th>
              <th>Роли</th>
              <th>Superuser</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td className="code">{user.id}</td>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>
                  <span className="badge">{user.is_active ? "active" : "inactive"}</span>
                </td>
                <td>{user.roles.map((role) => role.name).join(", ") || "-"}</td>
                <td>{user.is_superuser ? "yes" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DashboardShell>
  );
}
