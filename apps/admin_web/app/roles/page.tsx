'use client';

import { useEffect, useState } from "react";
import { DashboardShell } from "../components/DashboardShell";
import { fetchMe, fetchRoles } from "../lib/api";
import type { Role, User } from "../lib/types";

export default function RolesPage() {
  const [me, setMe] = useState<User | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);

  useEffect(() => {
    async function load() {
      const [meData, rolesData] = await Promise.all([fetchMe(), fetchRoles()]);
      setMe(meData);
      setRoles(rolesData);
    }
    load();
  }, []);

  return (
    <DashboardShell title="Роли" subtitle="Текущие роли и связанные права" currentUser={me}>
      <div className="table-wrap">
        <div className="table-toolbar">
          <div>
            <div className="table-title">Роли</div>
            <div className="table-sub">Данные приходят из /api/v1/roles</div>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Роль</th>
              <th>Slug</th>
              <th>Описание</th>
              <th>Permissions</th>
            </tr>
          </thead>
          <tbody>
            {roles.map((role) => (
              <tr key={role.id}>
                <td className="code">{role.id}</td>
                <td>{role.name}</td>
                <td className="code">{role.slug}</td>
                <td>{role.description ?? "-"}</td>
                <td>{role.permissions.map((permission) => permission.key).join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DashboardShell>
  );
}
