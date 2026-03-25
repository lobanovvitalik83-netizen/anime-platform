"use client";
import React, { useEffect, useMemo, useState } from "react";
import { LayoutDashboard, Users, ShieldCheck, KeyRound, Settings, Search, RefreshCw, LogOut, Loader2, CheckCircle2, AlertCircle, UserPlus, Plus, Database, UserCircle2, FolderKanban, Bot, Save } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type Permission = { id: number; key: string; description: string };
type Role = { id: number; name: string; slug?: string; description?: string; permissions?: Permission[] };
type UserItem = { id: number; email: string; username: string; is_active: boolean; is_superuser?: boolean; roles?: Role[] };
type ContentItem = { id: number; title: string; description: string; tags: string; media_type: string; media_path?: string | null; status: string; visibility: string; is_archived: boolean };
type SettingsData = { project_name: string; support_email: string; telegram_bot_enabled: boolean; telegram_bot_username: string; telegram_admin_chat_id: string };
type LoginResponse = { access_token: string; refresh_token: string; token_type: string };
type AppSection = "dashboard" | "content" | "users" | "roles" | "permissions" | "settings";

const navItems = [
  { id: "dashboard", label: "Дашборд", icon: LayoutDashboard },
  { id: "content", label: "Контент", icon: FolderKanban },
  { id: "users", label: "Пользователи", icon: Users },
  { id: "roles", label: "Роли", icon: ShieldCheck },
  { id: "permissions", label: "Permissions", icon: KeyRound },
  { id: "settings", label: "Настройки и бот", icon: Bot },
] as const;

const cn = (...items:(string | false | null | undefined)[]) => items.filter(Boolean).join(" ");

function MetricCard({ title, value, subtitle, icon: Icon }:{title:string; value:string|number; subtitle:string; icon:any}) {
  return <div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="flex items-start justify-between gap-4"><div><div className="text-sm text-slate-400">{title}</div><div className="mt-3 text-4xl font-semibold tracking-tight text-white">{value}</div><div className="mt-2 text-sm text-sky-300">{subtitle}</div></div><div className="rounded-2xl border border-sky-400/20 bg-sky-400/10 p-3 text-sky-300"><Icon className="h-5 w-5" /></div></div></div>;
}
function StatusPill({ ok, text }:{ok:boolean; text:string}) {
  return <span className={cn("inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium", ok ? "border-emerald-400/20 bg-emerald-500/10 text-emerald-300":"border-amber-400/20 bg-amber-500/10 text-amber-200")}>{ok ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertCircle className="h-3.5 w-3.5" />}{text}</span>;
}
async function parseJsonSafe(response: Response) { const text = await response.text(); try { return text ? JSON.parse(text) : null; } catch { return text; } }

export default function AdminApp(){
  const [section, setSection] = useState<AppSection>("dashboard");
  const [loginValue, setLoginValue] = useState("owner");
  const [passwordValue, setPasswordValue] = useState("ChangeThisOwnerPassword123!");
  const [accessToken, setAccessToken] = useState("");
  const [refreshToken, setRefreshToken] = useState("");
  const [isBooting, setIsBooting] = useState(true);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [health, setHealth] = useState<any>(null);
  const [me, setMe] = useState<UserItem | null>(null);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [settingsData, setSettingsData] = useState<SettingsData | null>(null);
  const [query, setQuery] = useState("");
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showCreateContent, setShowCreateContent] = useState(false);
  const [newUser, setNewUser] = useState({ email: "", username: "", password: "", role_id: "" });
  const [newContent, setNewContent] = useState({ title: "", description: "", tags: "", media_type: "image", status: "draft", visibility: "public" });
  const [contentFile, setContentFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const a = localStorage.getItem("anime_admin_access_token") || "";
    const r = localStorage.getItem("anime_admin_refresh_token") || "";
    if (a) setAccessToken(a);
    if (r) setRefreshToken(r);
    setIsBooting(false);
  }, []);

  useEffect(() => {
    if (accessToken) void loadAll(accessToken);
  }, [accessToken]);

  async function apiRequest(path:string, options:RequestInit={}, tokenOverride?:string) {
    const token = tokenOverride || accessToken;
    const headers = new Headers(options.headers || {});
    if (!(options.body instanceof FormData) && options.body && !headers.has("Content-Type")) headers.set("Content-Type","application/json");
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers, cache:"no-store" });
    const payload = await parseJsonSafe(response);
    if (!response.ok) {
      const message = typeof payload === "object" && payload && "detail" in payload ? String((payload as any).detail) : `HTTP ${response.status}`;
      throw new Error(message);
    }
    return payload;
  }

  async function loadAll(token:string) {
    setIsRefreshing(true);
    setErrorMessage("");
    try {
      const [h,m,u,r,p,c,s] = await Promise.all([
        apiRequest("/health", {}, token),
        apiRequest("/api/v1/auth/me", {}, token),
        apiRequest("/api/v1/users", {}, token),
        apiRequest("/api/v1/roles", {}, token),
        apiRequest("/api/v1/permissions", {}, token),
        apiRequest("/api/v1/content", {}, token),
        apiRequest("/api/v1/settings", {}, token),
      ]);
      setHealth(h); setMe(m); setUsers(Array.isArray(u)?u:[]); setRoles(Array.isArray(r)?r:[]);
      setPermissions(Array.isArray(p)?p:[]); setContent(Array.isArray(c)?c:[]); setSettingsData(s as SettingsData);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Ошибка загрузки данных");
    } finally {
      setIsRefreshing(false);
    }
  }

  async function handleLogin() {
    setIsLoggingIn(true); setErrorMessage("");
    try {
      const data = await apiRequest("/api/v1/auth/login",{method:"POST", body:JSON.stringify({email_or_username:loginValue,password:passwordValue})},"") as LoginResponse;
      setAccessToken(data.access_token); setRefreshToken(data.refresh_token);
      localStorage.setItem("anime_admin_access_token", data.access_token);
      localStorage.setItem("anime_admin_refresh_token", data.refresh_token);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Ошибка входа");
    } finally { setIsLoggingIn(false); }
  }

  async function handleRefreshTokens() {
    if (!refreshToken) return;
    try {
      const data = await apiRequest("/api/v1/auth/refresh",{method:"POST", body:JSON.stringify({refresh_token:refreshToken})},"") as LoginResponse;
      setAccessToken(data.access_token); setRefreshToken(data.refresh_token);
      localStorage.setItem("anime_admin_access_token", data.access_token);
      localStorage.setItem("anime_admin_refresh_token", data.refresh_token);
      await loadAll(data.access_token);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Не удалось обновить токен");
    }
  }

  function handleLogout() {
    localStorage.removeItem("anime_admin_access_token");
    localStorage.removeItem("anime_admin_refresh_token");
    setAccessToken(""); setRefreshToken(""); setMe(null); setUsers([]); setRoles([]); setPermissions([]); setContent([]); setSettingsData(null);
  }

  async function createUser() {
    setIsSaving(true); setMessage("");
    try {
      await apiRequest("/api/v1/users", { method:"POST", body: JSON.stringify({ email:newUser.email, username:newUser.username, password:newUser.password, role_ids:newUser.role_id ? [Number(newUser.role_id)] : [] }) });
      setMessage("Пользователь создан");
      setShowCreateUser(false);
      setNewUser({ email: "", username: "", password: "", role_id: "" });
      await loadAll(accessToken);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Не удалось создать пользователя");
    } finally { setIsSaving(false); }
  }

  async function createContent() {
    setIsSaving(true); setMessage("");
    try {
      const form = new FormData();
      form.append("title", newContent.title);
      form.append("description", newContent.description);
      form.append("tags", newContent.tags);
      form.append("media_type", newContent.media_type);
      form.append("status", newContent.status);
      form.append("visibility", newContent.visibility);
      if (contentFile) form.append("media_file", contentFile);
      await apiRequest("/api/v1/content", { method:"POST", body: form });
      setMessage("Карточка создана");
      setShowCreateContent(false);
      setNewContent({ title: "", description: "", tags: "", media_type: "image", status: "draft", visibility: "public" });
      setContentFile(null);
      await loadAll(accessToken);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Не удалось создать карточку");
    } finally { setIsSaving(false); }
  }

  async function archiveContent(item: ContentItem) {
    try {
      await apiRequest(`/api/v1/content/${item.id}`, { method:"PATCH", body: JSON.stringify({ is_archived: !item.is_archived }) });
      await loadAll(accessToken);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Не удалось изменить карточку");
    }
  }

  async function saveSettings() {
    if (!settingsData) return;
    setIsSaving(true); setMessage("");
    try {
      await apiRequest("/api/v1/settings", { method:"PATCH", body: JSON.stringify(settingsData) });
      setMessage("Настройки сохранены");
      await loadAll(accessToken);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Не удалось сохранить настройки");
    } finally { setIsSaving(false); }
  }

  const filteredUsers = useMemo(() => !query.trim() ? users : users.filter(u => `${u.username} ${u.email}`.toLowerCase().includes(query.toLowerCase())), [users, query]);
  const filteredRoles = useMemo(() => !query.trim() ? roles : roles.filter(r => `${r.name} ${r.slug || ""}`.toLowerCase().includes(query.toLowerCase())), [roles, query]);
  const filteredPermissions = useMemo(() => !query.trim() ? permissions : permissions.filter(p => `${p.key} ${p.description}`.toLowerCase().includes(query.toLowerCase())), [permissions, query]);
  const filteredContent = useMemo(() => !query.trim() ? content : content.filter(c => `${c.title} ${c.description} ${c.tags}`.toLowerCase().includes(query.toLowerCase())), [content, query]);

  if (isBooting) return <div className="flex min-h-screen items-center justify-center bg-[#071226] text-white"><div className="flex items-center gap-3 text-lg"><Loader2 className="h-5 w-5 animate-spin" />Загрузка панели...</div></div>;

  if (!accessToken) {
    return <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,rgba(80,70,229,0.22),transparent_28%),radial-gradient(circle_at_top_left,rgba(59,130,246,0.18),transparent_25%),#071226] px-6 py-10 text-white"><div className="mx-auto grid min-h-[80vh] max-w-7xl grid-cols-1 gap-10 lg:grid-cols-[1.1fr_0.9fr]"><div className="flex items-center"><div className="max-w-2xl"><div className="inline-flex items-center gap-2 rounded-full border border-sky-400/20 bg-sky-400/10 px-4 py-2 text-sm text-sky-300"><Database className="h-4 w-4" />Полный admin + backend + tg bot</div><h1 className="mt-6 text-5xl font-bold tracking-tight">Anime Platform Admin</h1><p className="mt-5 text-lg leading-8 text-slate-300">Теперь здесь реальные разделы для контента, пользователей, ролей, permissions и настроек Telegram-бота.</p></div></div><div className="flex items-center justify-center"><div className="w-full max-w-md rounded-[32px] border border-white/10 bg-[#0b1630]/90 p-7"><div className="mb-6"><div className="text-4xl font-bold">Вход</div><div className="mt-2 text-slate-400">Авторизация в рабочую панель</div></div><div className="space-y-4"><input value={loginValue} onChange={(e)=>setLoginValue(e.target.value)} className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" placeholder="owner" /><input type="password" value={passwordValue} onChange={(e)=>setPasswordValue(e.target.value)} className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" placeholder="Пароль" />{errorMessage ? <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{errorMessage}</div> : null}<button onClick={handleLogin} disabled={isLoggingIn} className="w-full rounded-2xl bg-gradient-to-r from-blue-600 to-violet-600 px-4 py-3 font-semibold text-white">{isLoggingIn ? "Входим..." : "Войти"}</button></div></div></div></div></div>;
  }

  return <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,rgba(80,70,229,0.18),transparent_28%),radial-gradient(circle_at_top_left,rgba(59,130,246,0.16),transparent_25%),#071226] text-white"><div className="flex min-h-screen"><aside className="w-[260px] shrink-0 border-r border-white/10 bg-[#0a1530]/80 px-5 py-6"><div className="mb-10 text-3xl font-bold tracking-tight">Anime<span className="text-sky-400">Platform</span></div><nav className="space-y-3">{navItems.map((item)=>{ const Icon=item.icon; return <button key={item.id} onClick={()=>setSection(item.id)} className={cn("flex w-full items-center gap-3 rounded-2xl border px-4 py-3 text-left transition", section===item.id ? "border-sky-400/20 bg-sky-400/10 text-white" : "border-white/10 bg-white/[0.03] text-slate-300 hover:bg-white/[0.05]")}><Icon className="h-4 w-4" />{item.label}</button>; })}<button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-left text-slate-300"><LogOut className="h-4 w-4" />Выйти</button></nav></aside><main className="flex-1 px-6 py-7"><div className="mb-8 flex items-start justify-between gap-4"><div><h1 className="text-4xl font-bold tracking-tight">{section==="dashboard"&&"Дашборд"}{section==="content"&&"Контент"}{section==="users"&&"Пользователи"}{section==="roles"&&"Роли"}{section==="permissions"&&"Permissions"}{section==="settings"&&"Настройки и бот"}</h1><div className="mt-2 text-slate-400">Рабочие разделы только на живых данных.</div></div><div className="flex items-center gap-3"><div className="relative"><Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" /><input value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Поиск" className="rounded-2xl border border-white/10 bg-white/[0.04] py-3 pl-10 pr-4 text-sm text-white outline-none" /></div><button onClick={()=>loadAll(accessToken)} disabled={isRefreshing} className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-200"><RefreshCw className={cn("h-4 w-4",isRefreshing&&"animate-spin")} />Обновить</button></div></div>{message ? <div className="mb-4 rounded-2xl border border-sky-400/20 bg-sky-400/10 px-4 py-3 text-sm text-sky-100">{message}</div> : null}{errorMessage ? <div className="mb-4 rounded-2xl border border-amber-400/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">{errorMessage}</div> : null}
{section==="dashboard" && <div className="space-y-6"><div className="grid grid-cols-1 gap-5 xl:grid-cols-5"><MetricCard title="Пользователи" value={users.length} subtitle="Из backend" icon={Users} /><MetricCard title="Роли" value={roles.length} subtitle="RBAC" icon={ShieldCheck} /><MetricCard title="Permissions" value={permissions.length} subtitle="Права" icon={KeyRound} /><MetricCard title="Карточки" value={content.length} subtitle="Контент" icon={FolderKanban} /><MetricCard title="API" value={health?.status || "unknown"} subtitle="Статус сервиса" icon={Database} /></div></div>}
{section==="content" && <div className="space-y-6"><div className="flex flex-wrap items-center justify-between gap-3"><div className="text-slate-400">Создание, загрузка файла и архивация карточек работают через backend.</div><button onClick={()=>setShowCreateContent(v=>!v)} className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-blue-600 to-violet-600 px-4 py-3 text-sm font-medium text-white"><Plus className="h-4 w-4" />{showCreateContent ? "Скрыть форму" : "Создать карточку"}</button></div>{showCreateContent && <div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="mb-4 text-xl font-semibold">Новая карточка</div><div className="grid grid-cols-1 gap-4 md:grid-cols-2"><input value={newContent.title} onChange={(e)=>setNewContent(s=>({...s,title:e.target.value}))} placeholder="Название" className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" /><select value={newContent.media_type} onChange={(e)=>setNewContent(s=>({...s,media_type:e.target.value}))} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"><option value="image">Фото</option><option value="video">Видео</option></select><textarea value={newContent.description} onChange={(e)=>setNewContent(s=>({...s,description:e.target.value}))} placeholder="Описание" rows={4} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none md:col-span-2" /><input value={newContent.tags} onChange={(e)=>setNewContent(s=>({...s,tags:e.target.value}))} placeholder="Теги через запятую" className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" /><input type="file" accept={newContent.media_type === "video" ? "video/*" : "image/*"} onChange={(e)=>setContentFile(e.target.files?.[0] || null)} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" /><select value={newContent.status} onChange={(e)=>setNewContent(s=>({...s,status:e.target.value}))} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"><option value="draft">draft</option><option value="published">published</option></select><select value={newContent.visibility} onChange={(e)=>setNewContent(s=>({...s,visibility:e.target.value}))} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"><option value="public">public</option><option value="private">private</option><option value="hidden">hidden</option></select></div><div className="mt-4"><button onClick={createContent} disabled={isSaving} className="rounded-2xl border border-sky-400/20 bg-sky-400/10 px-4 py-3 text-sm text-sky-100">{isSaving ? "Сохранение..." : "Сохранить карточку"}</button></div></div>}<div className="grid grid-cols-1 gap-4 xl:grid-cols-2">{filteredContent.map((item)=><div key={item.id} className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="flex items-start justify-between gap-4"><div><div className="text-2xl font-semibold">{item.title}</div><div className="mt-2 text-sm text-slate-300">{item.description}</div><div className="mt-3 flex flex-wrap gap-2"><StatusPill ok={item.status==="published"} text={item.status} /><StatusPill ok={!item.is_archived} text={item.is_archived ? "archived" : "active"} /></div><div className="mt-3 text-xs text-slate-400">{item.tags}</div>{item.media_path ? <a className="mt-3 inline-block text-sm text-sky-300 underline" href={`${API_BASE}${item.media_path}`} target="_blank">Открыть файл</a> : null}</div><button onClick={()=>archiveContent(item)} className="rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-slate-200">{item.is_archived ? "Разархивировать" : "Архивировать"}</button></div></div>)}</div></div>}
{section==="users" && <div className="space-y-6"><div className="flex flex-wrap items-center justify-between gap-3"><div className="text-slate-400">Создание пользователя идёт в живой backend.</div><button onClick={()=>setShowCreateUser(v=>!v)} className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-blue-600 to-violet-600 px-4 py-3 text-sm font-medium text-white"><UserPlus className="h-4 w-4" />{showCreateUser ? "Скрыть форму" : "Создать пользователя"}</button></div>{showCreateUser && <div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="mb-4 text-xl font-semibold">Новый пользователь</div><div className="grid grid-cols-1 gap-4 md:grid-cols-2"><input value={newUser.email} onChange={(e)=>setNewUser(s=>({...s,email:e.target.value}))} placeholder="email" className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" /><input value={newUser.username} onChange={(e)=>setNewUser(s=>({...s,username:e.target.value}))} placeholder="username" className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" /><input type="password" value={newUser.password} onChange={(e)=>setNewUser(s=>({...s,password:e.target.value}))} placeholder="password" className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" /><select value={newUser.role_id} onChange={(e)=>setNewUser(s=>({...s,role_id:e.target.value}))} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"><option value="">Без роли</option>{roles.map(role=><option key={role.id} value={role.id}>{role.name}</option>)}</select></div><div className="mt-4"><button onClick={createUser} disabled={isSaving} className="rounded-2xl border border-sky-400/20 bg-sky-400/10 px-4 py-3 text-sm text-sky-100">{isSaving ? "Создание..." : "Создать"}</button></div></div>}<div className="overflow-hidden rounded-3xl border border-white/10 bg-[#0f1834]"><table className="w-full border-collapse text-left"><thead className="border-b border-white/10 bg-white/[0.03] text-sm text-slate-400"><tr><th className="px-5 py-4 font-medium">ID</th><th className="px-5 py-4 font-medium">Username</th><th className="px-5 py-4 font-medium">Email</th><th className="px-5 py-4 font-medium">Статус</th><th className="px-5 py-4 font-medium">Роли</th></tr></thead><tbody>{filteredUsers.map(user=><tr key={user.id} className="border-b border-white/5 text-sm last:border-b-0"><td className="px-5 py-4 text-slate-300">{user.id}</td><td className="px-5 py-4 text-white">{user.username}</td><td className="px-5 py-4 text-slate-300">{user.email}</td><td className="px-5 py-4"><StatusPill ok={user.is_active} text={user.is_active ? "active" : "inactive"} /></td><td className="px-5 py-4 text-slate-300">{(user.roles || []).map(r=>r.name).join(", ") || "—"}</td></tr>)}</tbody></table></div></div>}
{section==="roles" && <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">{filteredRoles.map(role=><div key={role.id} className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="text-2xl font-semibold">{role.name}</div><div className="mt-2 text-sm text-slate-400">slug: {role.slug || "—"}</div><div className="mt-4 text-sm text-slate-300">{role.description || "Без описания"}</div><div className="mt-5 flex flex-wrap gap-2">{(role.permissions || []).map(permission=><span key={permission.id} className="rounded-full border border-sky-400/20 bg-sky-400/10 px-3 py-1 text-xs text-sky-200">{permission.key}</span>)}</div></div>)}</div>}
{section==="permissions" && <div className="overflow-hidden rounded-3xl border border-white/10 bg-[#0f1834]"><table className="w-full border-collapse text-left"><thead className="border-b border-white/10 bg-white/[0.03] text-sm text-slate-400"><tr><th className="px-5 py-4 font-medium">ID</th><th className="px-5 py-4 font-medium">Key</th><th className="px-5 py-4 font-medium">Description</th></tr></thead><tbody>{filteredPermissions.map(permission=><tr key={permission.id} className="border-b border-white/5 text-sm last:border-b-0"><td className="px-5 py-4 text-slate-300">{permission.id}</td><td className="px-5 py-4 text-white">{permission.key}</td><td className="px-5 py-4 text-slate-300">{permission.description}</td></tr>)}</tbody></table></div>}
{section==="settings" && settingsData && <div className="grid grid-cols-1 gap-6 xl:grid-cols-2"><div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="mb-4 flex items-center gap-2 text-2xl font-semibold"><Settings className="h-5 w-5" />Настройки проекта</div><div className="space-y-4"><input value={settingsData.project_name} onChange={(e)=>setSettingsData(s=>s?({...s,project_name:e.target.value}):s)} className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" placeholder="Название проекта" /><input value={settingsData.support_email} onChange={(e)=>setSettingsData(s=>s?({...s,support_email:e.target.value}):s)} className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" placeholder="Support email" /></div></div><div className="rounded-3xl border border-white/10 bg-[#0f1834] p-6"><div className="mb-4 flex items-center gap-2 text-2xl font-semibold"><Bot className="h-5 w-5" />Telegram Bot</div><div className="space-y-4"><label className="flex items-center gap-3 text-sm text-slate-300"><input type="checkbox" checked={settingsData.telegram_bot_enabled} onChange={(e)=>setSettingsData(s=>s?({...s,telegram_bot_enabled:e.target.checked}):s)} /> Бот включён</label><input value={settingsData.telegram_bot_username} onChange={(e)=>setSettingsData(s=>s?({...s,telegram_bot_username:e.target.value}):s)} className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" placeholder="@bot_username" /><input value={settingsData.telegram_admin_chat_id} onChange={(e)=>setSettingsData(s=>s?({...s,telegram_admin_chat_id:e.target.value}):s)} className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none" placeholder="admin chat id" /><button onClick={saveSettings} disabled={isSaving} className="inline-flex items-center gap-2 rounded-2xl border border-sky-400/20 bg-sky-400/10 px-4 py-3 text-sm text-sky-100"><Save className="h-4 w-4" />{isSaving ? "Сохранение..." : "Сохранить настройки"}</button></div></div></div>}
</main></div></div>;
}
