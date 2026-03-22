'use client';

import { useEffect, useState } from "react";
import { DashboardShell } from "../components/DashboardShell";
import { fetchMe, fetchPermissions } from "../lib/api";
import type { Permission, User } from "../lib/types";

export default function PermissionsPage() {
  const [me, setMe] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<Permission[]>([]);

  useEffect(() => {
    async function load() {
      const [meData, permissionsData] = await Promise.all([fetchMe(), fetchPermissions()]);
      setMe(meData);
      setPermissions(permissionsData);
    }
    load();
  }, []);

  return (
    <DashboardShell title="Permissions" subtitle="Все права доступа системы" currentUser={me}>
      <div className="table-wrap">
        <div className="table-toolbar">
          <div>
            <div className="table-title">Permissions</div>
            <div className="table-sub">Данные приходят из /api/v1/permissions</div>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Key</th>
              <th>Описание</th>
            </tr>
          </thead>
          <tbody>
            {permissions.map((permission) => (
              <tr key={permission.id}>
                <td className="code">{permission.id}</td>
                <td className="code">{permission.key}</td>
                <td>{permission.description ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DashboardShell>
  );
}
