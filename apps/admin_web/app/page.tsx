
"use client";

import React, { useEffect, useMemo, useState } from "react";
import { LayoutDashboard, Users, ShieldCheck, KeyRound, Settings, Search, RefreshCw, LogOut, Loader2, CheckCircle2, AlertCircle, UserPlus, Plus, Database, UserCircle2, FolderKanban, Upload, Save } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://185.250.45.184:8000";

type Permission = { id: number; key: string; description: string };
type Role = { id: number; name: string; slug?: string; description?: string; permissions?: Permission[] };
type UserItem = { id: number; email: string; username: string; is_active: boolean; is_superuser?: boolean; created_at?: string; updated_at?: string; roles?: Role[]; permissions?: Permission[] };
type ContentItem = { id: number; title: string; description: string; tags: string[]; media_type?: string | null; media_path?: string | null; status: string; visibility: string; created_at: string; updated_at: string };
type SettingItem = { key: string; value: string };
type AnalyticsSummary = { users_total: number; roles_total: number; permissions_total: number; content_total: number; content_published: number; content_draft: number; content_archived: number };
type LoginResponse = { access_token: string; refresh_token: string; token_type: string };
type AppSection = "dashboard" | "users" | "roles" | "permissions" | "content" | "settings" | "account";

const navItems: { id: AppSection; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "dashboard", label: "Дашборд", icon: LayoutDashboard },
  { id: "users", label: "Пользователи", icon: Users },
  { id: "roles", label: "Роли", icon: ShieldCheck },
  { id: "permissions", label: "Permissions", icon: KeyRound },
  { id: "content", label: "Контент", icon: FolderKanban },
  { id: "settings", label: "Настройки", icon: Settings },
  { id: "account", label: "Аккаунт", icon: UserCircle2 },
];

function cn(...items: Array<string | false | null | undefined>) { return items.filter(Boolean).join(" "); }
function MetricCard({ title, value, subtitle, icon: Icon }: { title: string; value: string | number; subtitle: string; icon: React.ComponentType<{ className?: string }> }) {
  return <div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="flex items-start justify-between gap-4"><div><div className="text-sm text-slate-400">{title}</div><div className="mt-3 text-4xl font-semibold tracking-tight text-white">{value}</div><div className="mt-2 text-sm text-sky-300">{subtitle}</div></div><div className="rounded-2xl border border-sky-400/20 bg-sky-400/10 p-3 text-sky-300"><Icon className="h-5 w-5" /></div></div></div>;
}
function StatusPill({ ok, text }: { ok: boolean; text: string }) {
  return <span className={cn("inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium", ok ? "border-emerald-400/20 bg-emerald-500/10 text-emerald-300" : "border-amber-400/20 bg-amber-500/10 text-amber-200")}>{ok ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertCircle className="h-3.5 w-3.5" />}{text}</span>;
}
async function parseJsonSafe(response: Response) { const text = await response.text(); try { return text ? JSON.parse(text) : null; } catch { return text; } }

export default function AdminApp() {
  const [section, setSection] = useState<AppSection>("dashboard");
  const [loginValue, setLoginValue] = useState("owner");
  const [passwordValue, setPasswordValue] = useState("ChangeThisOwnerPassword123!");
  const [accessToken, setAccessToken] = useState("");
  const [refreshToken, setRefreshToken] = useState("");
  const [isBooting, setIsBooting] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [me, setMe] = useState<UserItem | null>(null);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [contentItems, setContentItems] = useState<ContentItem[]>([]);
  const [settingsItems, setSettingsItems] = useState<SettingItem[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [query, setQuery] = useState("");
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showCreateContent, setShowCreateContent] = useState(false);
  const [newUser, setNewUser] = useState({ email: "", username: "", password: "", role_id: "" });
  const [newContent, setNewContent] = useState({ title: "", description: "", tags: "", status: "draft", visibility: "public" });
  const [contentFile, setContentFile] = useState<File | null>(null);
  const [flash, setFlash] = useState("");

  useEffect(() => {
    const savedAccess = typeof window !== "undefined" ? window.localStorage.getItem("anime_admin_access_token") : "";
    const savedRefresh = typeof window !== "undefined" ? window.localStorage.getItem("anime_admin_refresh_token") : "";
    if (savedAccess) setAccessToken(savedAccess);
    if (savedRefresh) setRefreshToken(savedRefresh);
    setIsBooting(false);
  }, []);

  useEffect(() => { if (accessToken) void loadAll(accessToken); }, [accessToken]);

  async function apiRequest(path: string, options: RequestInit = {}, tokenOverride?: string) {
    const token = tokenOverride || accessToken;
    const headers = new Headers(options.headers || {});
    if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers, cache: "no-store" });
    const payload = await parseJsonSafe(response);
    if (!response.ok) {
      const message = typeof payload === "object" && payload && "detail" in payload ? String((payload as any).detail) : `HTTP ${response.status}`;
      throw new Error(message);
    }
    return payload;
  }

  async function loadAll(token: string) {
    setIsLoading(true);
    setErrorMessage("");
    try {
      const [meData, usersData, rolesData, permissionsData, contentData, settingsData, analyticsData] = await Promise.all([
        apiRequest("/api/v1/auth/me", {}, token),
        apiRequest("/api/v1/users", {}, token),
        apiRequest("/api/v1/roles", {}, token),
        apiRequest("/api/v1/permissions", {}, token),
        apiRequest("/api/v1/content", {}, token),
        apiRequest("/api/v1/settings", {}, token),
        apiRequest("/api/v1/analytics/summary", {}, token),
      ]);
      setMe(meData as UserItem);
      setUsers(Array.isArray(usersData) ? usersData as UserItem[] : []);
      setRoles(Array.isArray(rolesData) ? rolesData as Role[] : []);
      setPermissions(Array.isArray(permissionsData) ? permissionsData as Permission[] : []);
      setContentItems(Array.isArray(contentData) ? contentData as ContentItem[] : []);
      setSettingsItems(Array.isArray(settingsData) ? settingsData as SettingItem[] : []);
      setAnalytics(analyticsData as AnalyticsSummary);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Ошибка загрузки данных");
    } finally { setIsLoading(false); }
  }

  async function handleLogin() {
    setIsLoading(true); setErrorMessage("");
    try {
      const data = (await apiRequest("/api/v1/auth/login", { method: "POST", body: JSON.stringify({ email_or_username: loginValue, password: passwordValue }) }, "")) as LoginResponse;
      setAccessToken(data.access_token); setRefreshToken(data.refresh_token);
      if (typeof window !== "undefined") {
        window.localStorage.setItem("anime_admin_access_token", data.access_token);
        window.localStorage.setItem("anime_admin_refresh_token", data.refresh_token);
      }
    } catch (error) { setErrorMessage(error instanceof Error ? error.message : "Ошибка входа"); }
    finally { setIsLoading(false); }
  }

  async function handleRefreshTokens() {
    try {
      const data = (await apiRequest("/api/v1/auth/refresh", { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) }, "")) as LoginResponse;
      setAccessToken(data.access_token); setRefreshToken(data.refresh_token);
      if (typeof window !== "undefined") {
        window.localStorage.setItem("anime_admin_access_token", data.access_token);
        window.localStorage.setItem("anime_admin_refresh_token", data.refresh_token);
      }
      setFlash("Токен обновлён.");
    } catch (error) { setErrorMessage(error instanceof Error ? error.message : "Не удалось обновить токены"); }
  }

  function handleLogout() {
    setAccessToken(""); setRefreshToken(""); setMe(null);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("anime_admin_access_token");
      window.localStorage.removeItem("anime_admin_refresh_token");
    }
  }

  async function handleCreateUser() {
    try {
      await apiRequest("/api/v1/users", { method: "POST", body: JSON.stringify({ email: newUser.email, username: newUser.username, password: newUser.password, role_ids: newUser.role_id ? [Number(newUser.role_id)] : [] }) });
      setShowCreateUser(false);
      setNewUser({ email: "", username: "", password: "", role_id: "" });
      setFlash("Пользователь создан.");
      await loadAll(accessToken);
    } catch (error) { setErrorMessage(error instanceof Error ? error.message : "Не удалось создать пользователя"); }
  }

  async function handleCreateContent() {
    try {
      const created = await apiRequest("/api/v1/content", {
        method: "POST",
        body: JSON.stringify({
          title: newContent.title,
          description: newContent.description,
          tags: newContent.tags.split(",").map((x) => x.trim()).filter(Boolean),
          status: newContent.status,
          visibility: newContent.visibility,
        }),
      }) as ContentItem;

      if (contentFile) {
        const form = new FormData();
        form.append("file", contentFile);
        await apiRequest(`/api/v1/content/${created.id}/upload-media`, { method: "POST", body: form });
      }
      setShowCreateContent(false);
      setNewContent({ title: "", description: "", tags: "", status: "draft", visibility: "public" });
      setContentFile(null);
      setFlash("Карточка создана.");
      await loadAll(accessToken);
    } catch (error) { setErrorMessage(error instanceof Error ? error.message : "Не удалось создать карточку"); }
  }

  async function handleSaveSettings() {
    try {
      await apiRequest("/api/v1/settings", { method: "PATCH", body: JSON.stringify({ items: settingsItems }) });
      setFlash("Настройки сохранены.");
      await loadAll(accessToken);
    } catch (error) { setErrorMessage(error instanceof Error ? error.message : "Не удалось сохранить настройки"); }
  }

  const filteredUsers = useMemo(() => !query.trim() ? users : users.filter((u) => `${u.username} ${u.email}`.toLowerCase().includes(query.toLowerCase())), [users, query]);
  const filteredRoles = useMemo(() => !query.trim() ? roles : roles.filter((r) => `${r.name} ${r.slug || ""}`.toLowerCase().includes(query.toLowerCase())), [roles, query]);
  const filteredPermissions = useMemo(() => !query.trim() ? permissions : permissions.filter((p) => `${p.key} ${p.description}`.toLowerCase().includes(query.toLowerCase())), [permissions, query]);
  const filteredContent = useMemo(() => !query.trim() ? contentItems : contentItems.filter((c) => `${c.title} ${c.description} ${c.tags.join(" ")}`.toLowerCase().includes(query.toLowerCase())), [contentItems, query]);

  if (isBooting) return <div className="flex min-h-screen items-center justify-center bg-[#071226] text-white"><Loader2 className="h-5 w-5 animate-spin" /></div>;

  if (!accessToken) {
    return <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,rgba(80,70,229,0.22),transparent_28%),radial-gradient(circle_at_top_left,rgba(59,130,246,0.18),transparent_25%),#071226] px-6 py-10 text-white"><div className="mx-auto grid min-h-[80vh] max-w-7xl grid-cols-1 gap-10 lg:grid-cols-[1.1fr_0.9fr]"><div className="flex items-center"><div className="max-w-2xl"><div className="inline-flex items-center gap-2 rounded-full border border-sky-400/20 bg-sky-400/10 px-4 py-2 text-sm text-sky-300"><Database className="h-4 w-4" />Реальная admin-панель</div><h1 className="mt-6 text-5xl font-bold tracking-tight">Anime Platform Admin</h1><p className="mt-5 text-lg leading-8 text-slate-300">Работает на живых данных API, без фейковой статистики.</p></div></div><div className="flex items-center justify-center"><div className="w-full max-w-md rounded-[32px] border border-white/10 bg-[#0b1630]/90 p-7"><div className="mb-6"><div className="text-4xl font-bold">Вход</div><div className="mt-2 text-slate-400">Авторизация в рабочую панель</div></div><div className="space-y-4"><input value={loginValue} onChange={(e) => setLoginValue(e.target.value)} className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" placeholder="owner" /><input type="password" value={passwordValue} onChange={(e) => setPasswordValue(e.target.value)} className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" placeholder="Пароль" />{errorMessage ? <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{errorMessage}</div> : null}<button onClick={handleLogin} disabled={isLoading} className="w-full rounded-2xl bg-gradient-to-r from-blue-600 to-violet-600 px-4 py-3 font-semibold text-white">{isLoading ? "Входим..." : "Войти"}</button></div></div></div></div></div>;
  }

  return <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,rgba(80,70,229,0.18),transparent_28%),radial-gradient(circle_at_top_left,rgba(59,130,246,0.16),transparent_25%),#071226] text-white"><div className="flex min-h-screen"><aside className="w-[260px] shrink-0 border-r border-white/10 bg-[#0a1530]/80 px-5 py-6"><div className="mb-10 text-3xl font-bold tracking-tight">Anime<span className="text-sky-400">Platform</span></div><nav className="space-y-3">{navItems.map((item) => { const Icon = item.icon; return <button key={item.id} onClick={() => setSection(item.id)} className={cn("flex w-full items-center gap-3 rounded-2xl border px-4 py-3 text-left transition", section === item.id ? "border-sky-400/20 bg-sky-400/10 text-white" : "border-white/10 bg-white/[0.03] text-slate-300 hover:bg-white/[0.05]")}><Icon className="h-4 w-4" />{item.label}</button>; })}<button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-left text-slate-300 transition hover:bg-white/[0.05]"><LogOut className="h-4 w-4" />Выйти</button></nav></aside><main className="flex-1 px-6 py-7"><div className="mb-8 flex items-start justify-between gap-4"><div><h1 className="text-4xl font-bold tracking-tight">{navItems.find((x) => x.id === section)?.label}</h1><div className="mt-2 text-slate-400">Живые данные из backend</div></div><div className="flex items-center gap-3"><div className="relative"><Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Поиск" className="rounded-2xl border border-white/10 bg-white/[0.04] py-3 pl-10 pr-4 text-sm text-white outline-none" /></div><button onClick={() => loadAll(accessToken)} className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-200"><RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />Обновить</button></div></div>{errorMessage ? <div className="mb-4 rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{errorMessage}</div> : null}{flash ? <div className="mb-4 rounded-2xl border border-emerald-400/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">{flash}</div> : null}

{section === "dashboard" && <div className="space-y-6"><div className="grid grid-cols-1 gap-5 xl:grid-cols-4"><MetricCard title="Пользователи" value={analytics?.users_total || 0} subtitle="Реально из БД" icon={Users} /><MetricCard title="Роли" value={analytics?.roles_total || 0} subtitle="RBAC" icon={ShieldCheck} /><MetricCard title="Permissions" value={analytics?.permissions_total || 0} subtitle="Живые rights" icon={KeyRound} /><MetricCard title="Карточки" value={analytics?.content_total || 0} subtitle="Всего контента" icon={FolderKanban} /></div><div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_420px]"><div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="text-2xl font-semibold">Что реально подключено</div><div className="mt-5 flex flex-wrap gap-3"><StatusPill ok text="/auth/me" /><StatusPill ok text="/users" /><StatusPill ok text="/roles" /><StatusPill ok text="/permissions" /><StatusPill ok text="/content" /><StatusPill ok text="/settings" /><StatusPill ok text="/analytics/summary" /></div><div className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-3"><div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">Published: {analytics?.content_published || 0}</div><div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">Draft: {analytics?.content_draft || 0}</div><div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">Archived: {analytics?.content_archived || 0}</div></div></div><div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="text-sm text-slate-400">Текущий пользователь</div><div className="mt-3 text-4xl font-bold">{me?.username || "—"}</div><div className="mt-3 text-sky-300">{me?.email || "—"}</div><div className="mt-5 space-y-2 text-sm text-slate-300"><div>Superuser: {me?.is_superuser ? "yes" : "no"}</div><div>Активен: {me?.is_active ? "yes" : "no"}</div><div>Роли: {(me?.roles || []).map((role) => role.name).join(", ") || "нет"}</div></div></div></div></div>}

{section === "users" && <div className="space-y-6"><div className="flex flex-wrap items-center justify-between gap-3"><div className="text-slate-400">Создание пользователя работает через API.</div><button onClick={() => setShowCreateUser((v) => !v)} className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-blue-600 to-violet-600 px-4 py-3 text-sm font-medium text-white"><UserPlus className="h-4 w-4" />{showCreateUser ? "Скрыть форму" : "Создать пользователя"}</button></div>{showCreateUser ? <div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="mb-4 text-xl font-semibold">Новый пользователь</div><div className="grid grid-cols-1 gap-4 md:grid-cols-2"><input value={newUser.email} onChange={(e) => setNewUser((s) => ({ ...s, email: e.target.value }))} placeholder="email" className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" /><input value={newUser.username} onChange={(e) => setNewUser((s) => ({ ...s, username: e.target.value }))} placeholder="username" className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" /><input type="password" value={newUser.password} onChange={(e) => setNewUser((s) => ({ ...s, password: e.target.value }))} placeholder="password" className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" /><select value={newUser.role_id} onChange={(e) => setNewUser((s) => ({ ...s, role_id: e.target.value }))} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"><option value="">Без роли</option>{roles.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}</select></div><div className="mt-4 flex items-center gap-3"><button onClick={handleCreateUser} className="inline-flex items-center gap-2 rounded-2xl border border-sky-400/20 bg-sky-400/10 px-4 py-3 text-sm text-sky-100"><Plus className="h-4 w-4" />Создать</button></div></div> : null}<div className="overflow-hidden rounded-3xl border border-white/10 bg-[#0f1834]"><table className="w-full border-collapse text-left"><thead className="border-b border-white/10 bg-white/[0.03] text-sm text-slate-400"><tr><th className="px-5 py-4 font-medium">ID</th><th className="px-5 py-4 font-medium">Username</th><th className="px-5 py-4 font-medium">Email</th><th className="px-5 py-4 font-medium">Статус</th><th className="px-5 py-4 font-medium">Роли</th></tr></thead><tbody>{filteredUsers.map((user) => <tr key={user.id} className="border-b border-white/5 text-sm last:border-b-0"><td className="px-5 py-4 text-slate-300">{user.id}</td><td className="px-5 py-4 text-white">{user.username}</td><td className="px-5 py-4 text-slate-300">{user.email}</td><td className="px-5 py-4"><StatusPill ok={user.is_active} text={user.is_active ? "active" : "inactive"} /></td><td className="px-5 py-4 text-slate-300">{(user.roles || []).map((role) => role.name).join(", ") || "—"}</td></tr>)}</tbody></table></div></div>}

{section === "roles" && <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">{filteredRoles.map((role) => <div key={role.id} className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="text-2xl font-semibold">{role.name}</div><div className="mt-2 text-sm text-slate-400">slug: {role.slug || "—"}</div><div className="mt-4 text-sm text-slate-300">{role.description || "Без описания"}</div><div className="mt-5 flex flex-wrap gap-2">{(role.permissions || []).map((permission) => <span key={permission.id} className="rounded-full border border-sky-400/20 bg-sky-400/10 px-3 py-1 text-xs text-sky-200">{permission.key}</span>)}{!(role.permissions || []).length ? <span className="text-sm text-slate-500">Нет permissions</span> : null}</div></div>)}</div>}

{section === "permissions" && <div className="overflow-hidden rounded-3xl border border-white/10 bg-[#0f1834]"><table className="w-full border-collapse text-left"><thead className="border-b border-white/10 bg-white/[0.03] text-sm text-slate-400"><tr><th className="px-5 py-4 font-medium">ID</th><th className="px-5 py-4 font-medium">Key</th><th className="px-5 py-4 font-medium">Description</th></tr></thead><tbody>{filteredPermissions.map((permission) => <tr key={permission.id} className="border-b border-white/5 text-sm last:border-b-0"><td className="px-5 py-4 text-slate-300">{permission.id}</td><td className="px-5 py-4 text-white">{permission.key}</td><td className="px-5 py-4 text-slate-300">{permission.description}</td></tr>)}</tbody></table></div>}

{section === "content" && <div className="space-y-6"><div className="flex flex-wrap items-center justify-between gap-3"><div className="text-slate-400">Карточки контента и загрузка файла работают через API.</div><button onClick={() => setShowCreateContent((v) => !v)} className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-blue-600 to-violet-600 px-4 py-3 text-sm font-medium text-white"><Plus className="h-4 w-4" />{showCreateContent ? "Скрыть форму" : "Создать карточку"}</button></div>{showCreateContent ? <div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="mb-4 text-xl font-semibold">Новая карточка</div><div className="grid grid-cols-1 gap-4 md:grid-cols-2"><input value={newContent.title} onChange={(e) => setNewContent((s) => ({ ...s, title: e.target.value }))} placeholder="Название" className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" /><input value={newContent.tags} onChange={(e) => setNewContent((s) => ({ ...s, tags: e.target.value }))} placeholder="Теги через запятую" className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" /><textarea value={newContent.description} onChange={(e) => setNewContent((s) => ({ ...s, description: e.target.value }))} placeholder="Описание" className="min-h-32 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none md:col-span-2" /><select value={newContent.status} onChange={(e) => setNewContent((s) => ({ ...s, status: e.target.value }))} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"><option value="draft">draft</option><option value="published">published</option><option value="archived">archived</option></select><select value={newContent.visibility} onChange={(e) => setNewContent((s) => ({ ...s, visibility: e.target.value }))} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"><option value="public">public</option><option value="hidden">hidden</option><option value="private">private</option></select><label className="rounded-2xl border border-dashed border-white/15 bg-white/[0.03] px-4 py-3 text-sm text-slate-300 md:col-span-2">Файл: <input type="file" className="ml-3" onChange={(e) => setContentFile(e.target.files?.[0] || null)} /></label></div><div className="mt-4"><button onClick={handleCreateContent} className="inline-flex items-center gap-2 rounded-2xl border border-sky-400/20 bg-sky-400/10 px-4 py-3 text-sm text-sky-100"><Upload className="h-4 w-4" />Создать и загрузить</button></div></div> : null}<div className="overflow-hidden rounded-3xl border border-white/10 bg-[#0f1834]"><table className="w-full border-collapse text-left"><thead className="border-b border-white/10 bg-white/[0.03] text-sm text-slate-400"><tr><th className="px-5 py-4 font-medium">ID</th><th className="px-5 py-4 font-medium">Название</th><th className="px-5 py-4 font-medium">Теги</th><th className="px-5 py-4 font-medium">Файл</th><th className="px-5 py-4 font-medium">Статус</th></tr></thead><tbody>{filteredContent.map((item) => <tr key={item.id} className="border-b border-white/5 text-sm last:border-b-0"><td className="px-5 py-4 text-slate-300">{item.id}</td><td className="px-5 py-4 text-white">{item.title}</td><td className="px-5 py-4 text-slate-300">{item.tags.join(", ") || "—"}</td><td className="px-5 py-4 text-slate-300">{item.media_path || "нет файла"}</td><td className="px-5 py-4"><StatusPill ok={item.status === "published"} text={item.status} /></td></tr>)}</tbody></table></div></div>}

{section === "settings" && <div className="space-y-6"><div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="mb-4 text-xl font-semibold">Системные настройки</div><div className="grid grid-cols-1 gap-4 md:grid-cols-2">{settingsItems.map((item, idx) => <label key={item.key} className="block"><div className="mb-2 text-sm text-slate-300">{item.key}</div><input value={item.value} onChange={(e) => setSettingsItems((prev) => prev.map((x, i) => i === idx ? { ...x, value: e.target.value } : x))} className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" /></label>)}</div><div className="mt-4"><button onClick={handleSaveSettings} className="inline-flex items-center gap-2 rounded-2xl border border-sky-400/20 bg-sky-400/10 px-4 py-3 text-sm text-sky-100"><Save className="h-4 w-4" />Сохранить настройки</button></div></div></div>}

{section === "account" && <div className="grid grid-cols-1 gap-6 xl:grid-cols-2"><div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="text-2xl font-semibold">Сессия</div><div className="mt-5 space-y-3 text-sm text-slate-300"><div>API base: {API_BASE}</div><div>Access token: {accessToken ? "загружен" : "нет"}</div><div>Refresh token: {refreshToken ? "загружен" : "нет"}</div></div><div className="mt-5 flex gap-3"><button onClick={handleRefreshTokens} className="rounded-2xl border border-sky-400/20 bg-sky-400/10 px-4 py-3 text-sm text-sky-100">Обновить токен</button><button onClick={() => loadAll(accessToken)} className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-200">Перечитать данные</button></div></div><div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="text-2xl font-semibold">Текущий пользователь</div><div className="mt-5 space-y-3 text-sm text-slate-300"><div>Username: {me?.username || "—"}</div><div>Email: {me?.email || "—"}</div><div>Active: {me?.is_active ? "yes" : "no"}</div><div>Superuser: {me?.is_superuser ? "yes" : "no"}</div><div>Roles: {(me?.roles || []).map((role) => role.name).join(", ") || "—"}</div></div></div></div>}
</main></div></div>;
}
