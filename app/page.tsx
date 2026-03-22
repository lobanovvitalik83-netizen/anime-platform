"use client";

import React, { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Users,
  ShieldCheck,
  KeyRound,
  Bell,
  Search,
  Settings,
  PlugZap,
  Bot,
  ChevronRight,
  LogOut,
  Plus,
  Filter,
  CheckCircle2,
  XCircle,
  Pencil,
  Trash2,
  RefreshCw,
  BarChart3,
  FolderKanban,
  Image as ImageIcon,
  Video,
  Sparkles,
  Crown,
  Mail,
  Globe,
  Activity,
  Database,
  Menu,
  MoonStar,
} from "lucide-react";

const navItems = [
  { id: "dashboard", label: "Дашборд", icon: LayoutDashboard },
  { id: "content", label: "Контент", icon: FolderKanban },
  { id: "media", label: "Медиатека", icon: ImageIcon },
  { id: "users", label: "Команда", icon: Users },
  { id: "roles", label: "Роли и доступы", icon: ShieldCheck },
  { id: "security", label: "Безопасность", icon: KeyRound },
  { id: "integrations", label: "Интеграции", icon: PlugZap },
  { id: "analytics", label: "Аналитика", icon: BarChart3 },
  { id: "settings", label: "Настройки", icon: Settings },
] as const;

type ContentItem = {
  id: number;
  title: string;
  type: string;
  status: "draft" | "published" | "archived";
  visibility: "public" | "hidden" | "private";
  code: string;
  cover: string;
  updated: string;
  author: string;
  schedule: string;
  tags: string[];
};

const defaultUsers = [
  { id: 1, name: "Виталий Лобанов", username: "owner", email: "owner@example.com", role: "Owner", status: "active", twoFA: true, directAccess: ["users.create", "roles.assign", "content.publish"] },
  { id: 2, name: "Марина Контент", username: "creator.marina", email: "creator@example.com", role: "Creator", status: "active", twoFA: false, directAccess: ["content.create", "content.update", "media.upload"] },
  { id: 3, name: "Илья Оператор", username: "operator.ilya", email: "operator@example.com", role: "Operator", status: "active", twoFA: true, directAccess: ["analytics.view"] },
] as const;

const defaultRoles = [
  { id: 1, name: "Owner", color: "linear-gradient(90deg,#d946ef,#22d3ee)", permissions: ["users.view", "users.create", "roles.assign", "content.publish", "settings.update"] },
  { id: 2, name: "Creator", color: "linear-gradient(90deg,#06b6d4,#3b82f6)", permissions: ["content.view", "content.create", "content.update", "media.upload"] },
  { id: 3, name: "Operator", color: "linear-gradient(90deg,#f59e0b,#f97316)", permissions: ["analytics.view", "logs.view"] },
];

const defaultContent: ContentItem[] = [
  { id: 101, title: "Attack on Titan Final Arc", type: "Аниме", status: "published", visibility: "public", code: "CARD-101", cover: "aot-final.jpg", updated: "сегодня, 18:40", author: "Марина Контент", schedule: "Опубликовано", tags: ["экшен", "финал"] },
  { id: 102, title: "Solo Leveling Special Clip", type: "Видео", status: "draft", visibility: "hidden", code: "CARD-102", cover: "solo-teaser.mp4", updated: "сегодня, 16:05", author: "Илья Оператор", schedule: "Черновик", tags: ["тизер", "new"] },
  { id: 103, title: "Your Name Collection", type: "Изображение", status: "archived", visibility: "private", code: "CARD-103", cover: "your-name.jpg", updated: "вчера, 23:11", author: "Виталий Лобанов", schedule: "Архив", tags: ["movie"] },
];

const defaultIntegrations = [
  { id: "telegram", name: "Telegram Bot", handle: "@anime_release_bot", state: "live", sync: true, description: "Основной production-бот для выдачи карточек и кодов." },
  { id: "vk", name: "VK Bot", handle: "vk.com/anime.release", state: "live", sync: true, description: "VK-бот синхронизирован с контентом." },
];

function cn(...classes: Array<string | false | undefined>) {
  return classes.filter(Boolean).join(" ");
}

function cardStyle() {
  return { border: "1px solid rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.04)", borderRadius: 28, padding: 24, boxShadow: "0 12px 40px rgba(0,0,0,0.25)" } as const;
}

function StatusBadge({ value }: { value: string }) {
  const styles: Record<string, React.CSSProperties> = {
    active: { background: "rgba(16,185,129,.15)", color: "#86efac", border: "1px solid rgba(16,185,129,.25)" },
    blocked: { background: "rgba(244,63,94,.15)", color: "#fda4af", border: "1px solid rgba(244,63,94,.25)" },
    published: { background: "rgba(16,185,129,.15)", color: "#86efac", border: "1px solid rgba(16,185,129,.25)" },
    draft: { background: "rgba(245,158,11,.15)", color: "#fcd34d", border: "1px solid rgba(245,158,11,.25)" },
    archived: { background: "rgba(148,163,184,.15)", color: "#cbd5e1", border: "1px solid rgba(148,163,184,.2)" },
    live: { background: "rgba(34,211,238,.15)", color: "#67e8f9", border: "1px solid rgba(34,211,238,.25)" },
    hidden: { background: "rgba(245,158,11,.15)", color: "#fcd34d", border: "1px solid rgba(245,158,11,.25)" },
    public: { background: "rgba(34,211,238,.15)", color: "#67e8f9", border: "1px solid rgba(34,211,238,.25)" },
    private: { background: "rgba(148,163,184,.15)", color: "#cbd5e1", border: "1px solid rgba(148,163,184,.2)" },
  };
  return <span style={{ ...styles[value], display: "inline-flex", alignItems: "center", borderRadius: 999, padding: "4px 10px", fontSize: 12, fontWeight: 600 }}>{value}</span>;
}

function MetricCard({ icon: Icon, label, value, caption }: { icon: React.ElementType; label: string; value: string | number; caption: string }) {
  return (
    <motion.div layout whileHover={{ y: -3 }} style={cardStyle()}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
        <div>
          <div style={{ color: "#94a3b8", fontSize: 14 }}>{label}</div>
          <div style={{ marginTop: 8, fontSize: 32, fontWeight: 700 }}>{value}</div>
          <div style={{ marginTop: 8, color: "#64748b", fontSize: 14 }}>{caption}</div>
        </div>
        <div style={{ borderRadius: 18, border: "1px solid rgba(34,211,238,.2)", background: "rgba(34,211,238,.1)", padding: 12, color: "#67e8f9", height: 48 }}>
          <Icon size={20} />
        </div>
      </div>
    </motion.div>
  );
}

function Drawer({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode }) {
  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 40, background: "rgba(2,6,23,.72)", backdropFilter: "blur(4px)" }} />
          <motion.div initial={{ x: 420, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 420, opacity: 0 }} transition={{ type: "spring", stiffness: 240, damping: 28 }} style={{ position: "fixed", right: 0, top: 0, zIndex: 50, width: "100%", maxWidth: 560, height: "100%", borderLeft: "1px solid rgba(255,255,255,.1)", background: "rgba(2,6,23,.96)", padding: 24, boxShadow: "0 12px 50px rgba(0,0,0,.45)", overflowY: "auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
              <div style={{ fontSize: 22, fontWeight: 700 }}>{title}</div>
              <button onClick={onClose} style={{ borderRadius: 18, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.05)", color: "#cbd5e1", padding: "10px 14px" }}>Закрыть</button>
            </div>
            {children}
          </motion.div>
        </>
      ) : null}
    </AnimatePresence>
  );
}

function Field({ label, value, onChange, placeholder, type = "text" }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string; type?: string }) {
  return (
    <label style={{ display: "block" }}>
      <div style={{ marginBottom: 8, fontSize: 14, color: "#cbd5e1" }}>{label}</div>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} style={{ width: "100%", borderRadius: 18, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.05)", color: "white", padding: "14px 16px", outline: "none" }} />
    </label>
  );
}

export default function Page() {
  const [loggedIn, setLoggedIn] = useState(true);
  const [activePage, setActivePage] = useState<(typeof navItems)[number]["id"]>("dashboard");
  const [search, setSearch] = useState("");
  const [users, setUsers] = useState([...defaultUsers]);
  const [roles, setRoles] = useState([...defaultRoles]);
  const [content, setContent] = useState<ContentItem[]>(defaultContent);
  const [integrations, setIntegrations] = useState([...defaultIntegrations]);
  const [notifications, setNotifications] = useState(["Панель готова к работе", "Telegram и VK синхронизированы"]);
  const [showForgot, setShowForgot] = useState(false);
  const [showUserDrawer, setShowUserDrawer] = useState(false);
  const [showRoleDrawer, setShowRoleDrawer] = useState(false);
  const [showContentDrawer, setShowContentDrawer] = useState(false);
  const [showIntegrationDrawer, setShowIntegrationDrawer] = useState(false);
  const [loginValue, setLoginValue] = useState("owner");
  const [passwordValue, setPasswordValue] = useState("ChangeThisOwnerPassword123!");
  const [forgotEmail, setForgotEmail] = useState("owner@example.com");
  const [newUser, setNewUser] = useState({ name: "", username: "", email: "", role: "Creator" });
  const [newRoleName, setNewRoleName] = useState("Creator Plus");
  const [newContent, setNewContent] = useState({ title: "", description: "", tags: "", mediaType: "image", mediaFileName: "", status: "draft", visibility: "public" });
  const [newIntegration, setNewIntegration] = useState({ name: "Telegram Bot 2", handle: "@new_release_bot", sync: true });

  const filteredContent = useMemo(() => content.filter((item) => `${item.title} ${item.type} ${item.code}`.toLowerCase().includes(search.toLowerCase())), [content, search]);
  const filteredUsers = useMemo(() => users.filter((u) => `${u.name} ${u.username} ${u.email}`.toLowerCase().includes(search.toLowerCase())), [users, search]);

  function notify(message: string) {
    setNotifications((prev) => [message, ...prev].slice(0, 4));
  }

  function addContentCard() {
    const id = Math.max(...content.map((c) => c.id)) + 1;
    setContent((prev) => [{ id, title: newContent.title || "Новая карточка", type: newContent.mediaType === "video" ? "Видео" : "Изображение", status: newContent.status as ContentItem["status"], visibility: newContent.visibility as ContentItem["visibility"], code: `CARD-${id}`, cover: newContent.mediaFileName || "Файл не загружен", updated: "только что", author: "Виталий Лобанов", schedule: "Без расписания", tags: newContent.tags ? newContent.tags.split(",").map((t) => t.trim()).filter(Boolean) : [] }, ...prev]);
    setNewContent({ title: "", description: "", tags: "", mediaType: "image", mediaFileName: "", status: "draft", visibility: "public" });
    setShowContentDrawer(false);
    notify("Карточка создана. Файл прикреплён к карточке.");
  }

  function addUser() {
    const id = users.length + 1;
    setUsers((prev) => [{ id, name: newUser.name || `Новый сотрудник ${id}`, username: newUser.username || `user.${id}`, email: newUser.email || `user${id}@example.com`, role: newUser.role, status: "active", twoFA: false, directAccess: [] }, ...prev]);
    setNewUser({ name: "", username: "", email: "", role: "Creator" });
    setShowUserDrawer(false);
    notify("Сотрудник создан.");
  }

  function addRole() {
    setRoles((prev) => [...prev, { id: prev.length + 1, name: newRoleName, color: "linear-gradient(90deg,#8b5cf6,#d946ef)", permissions: ["content.view", "content.create"] }]);
    setNewRoleName("Creator Plus");
    setShowRoleDrawer(false);
    notify("Роль создана.");
  }

  function addIntegration() {
    setIntegrations((prev) => [...prev, { id: `i-${prev.length + 1}`, name: newIntegration.name, handle: newIntegration.handle, state: "live", sync: newIntegration.sync, description: "Новая интеграция добавлена в систему." }]);
    setShowIntegrationDrawer(false);
    notify("Интеграция подключена.");
  }

  function toggleSync(id: string) {
    setIntegrations((prev) => prev.map((item) => (item.id === id ? { ...item, sync: !item.sync } : item)));
    notify("Синхронизация обновлена.");
  }

  function togglePublish(id: number) {
    setContent((prev) => prev.map((item) => (item.id === id ? { ...item, status: item.status === "published" ? "draft" : "published", updated: "только что" } : item)));
    notify("Статус карточки обновлён.");
  }

  function toggleVisibility(id: number) {
    setContent((prev) => prev.map((item) => (item.id === id ? { ...item, visibility: item.visibility === "public" ? "hidden" : "public", updated: "только что" } : item)));
    notify("Видимость карточки обновлена.");
  }

  function toggleArchive(id: number) {
    setContent((prev) => prev.map((item) => (item.id === id ? { ...item, status: item.status === "archived" ? "draft" : "archived", updated: "только что" } : item)));
    notify("Архив обновлён.");
  }

  function removeContent(id: number) {
    setContent((prev) => prev.filter((item) => item.id !== id));
    notify("Карточка удалена.");
  }

  function bulkAction(label: string) {
    notify(`${label} выполнено.`);
  }

  if (!loggedIn) {
    return <div />;
  }

  return (
    <div style={{ minHeight: "100vh", background: "#020617", color: "white" }}>
      <div style={{ position: "fixed", inset: 0, background: "radial-gradient(circle at top left, rgba(56,189,248,.16), transparent 25%), radial-gradient(circle at top right, rgba(168,85,247,.18), transparent 30%)", pointerEvents: "none" }} />
      <div style={{ position: "relative", display: "flex", minHeight: "100vh" }}>
        <aside style={{ width: 290, borderRight: "1px solid rgba(255,255,255,.1)", background: "rgba(2,6,23,.7)", padding: 20, display: "none" as const }} className="sidebar-desktop" />
        <aside style={{ width: 290, borderRight: "1px solid rgba(255,255,255,.1)", background: "rgba(2,6,23,.7)", padding: 20, backdropFilter: "blur(14px)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 28 }}>
            <div style={{ borderRadius: 18, background: "linear-gradient(135deg,#22d3ee,#8b5cf6)", padding: 12, color: "#020617" }}><Bot size={24} /></div>
            <div><div style={{ fontSize: 22, fontWeight: 700 }}>Anime Platform</div><div style={{ fontSize: 12, color: "#94a3b8" }}>Release control center</div></div>
          </div>
          <div style={{ borderRadius: 24, border: "1px solid rgba(217,70,239,.15)", background: "linear-gradient(135deg, rgba(217,70,239,.1), rgba(34,211,238,.1))", padding: 16, marginBottom: 18 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#f0abfc" }}><Crown size={16} /> Owner access</div>
            <div style={{ marginTop: 8, fontSize: 14, color: "#cbd5e1" }}>Полный контроль ролей, людей, безопасности, интеграций и контента.</div>
          </div>
          <nav style={{ display: "grid", gap: 8 }}>
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = activePage === item.id;
              return (
                <button key={item.id} onClick={() => setActivePage(item.id)} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderRadius: 18, padding: "14px 16px", border: active ? "1px solid rgba(34,211,238,.25)" : "1px solid transparent", background: active ? "rgba(34,211,238,.12)" : "rgba(255,255,255,.03)", color: active ? "white" : "#cbd5e1" }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 10 }}><Icon size={16} /> {item.label}</span>
                  <ChevronRight size={16} opacity={0.55} />
                </button>
              );
            })}
          </nav>
        </aside>

        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          <header style={{ position: "sticky", top: 0, zIndex: 20, borderBottom: "1px solid rgba(255,255,255,.1)", background: "rgba(2,6,23,.65)", backdropFilter: "blur(14px)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, padding: 16 }}>
              <button style={{ borderRadius: 16, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.04)", padding: 10 }}><Menu size={18} /></button>
              <div style={{ position: "relative", flex: 1, maxWidth: 680 }}>
                <Search size={16} style={{ position: "absolute", left: 16, top: "50%", transform: "translateY(-50%)", color: "#64748b" }} />
                <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Поиск по людям, ролям, контенту" style={{ width: "100%", borderRadius: 18, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.04)", color: "white", padding: "14px 16px 14px 42px" }} />
              </div>
              <button style={{ borderRadius: 16, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.04)", padding: 12 }}><Bell size={16} /></button>
              <button style={{ borderRadius: 16, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.04)", padding: 12 }}><MoonStar size={16} /></button>
              <button onClick={() => setLoggedIn(false)} style={{ borderRadius: 16, border: "1px solid rgba(244,63,94,.15)", background: "rgba(244,63,94,.1)", color: "#fecdd3", padding: "12px 16px", display: "flex", alignItems: "center", gap: 8 }}><LogOut size={16} /> Выйти</button>
            </div>
          </header>

          <main style={{ flex: 1, padding: 24 }}>
            {activePage === "dashboard" && (
              <div>
                <div style={{ marginBottom: 18, display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center" }}>
                  <div><div style={{ fontSize: 30, fontWeight: 700 }}>Дашборд</div><div style={{ color: "#94a3b8", marginTop: 4 }}>Релизная панель owner-уровня</div></div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 16 }}>
                  <MetricCard icon={Users} label="Сотрудники" value={users.length} caption="Owner / Creator / Operator" />
                  <MetricCard icon={ShieldCheck} label="Роли" value={roles.length} caption="RBAC и доступы" />
                  <MetricCard icon={FolderKanban} label="Контент" value={content.length} caption="Карточки и файлы" />
                  <MetricCard icon={PlugZap} label="Интеграции" value={integrations.length} caption="Telegram и VK" />
                </div>
                <div style={{ ...cardStyle(), marginTop: 20 }}>
                  <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 14 }}>Последние события</div>
                  <div style={{ display: "grid", gap: 10 }}>{notifications.map((note, i) => <div key={i} style={{ borderRadius: 16, border: "1px solid rgba(255,255,255,.08)", background: "rgba(255,255,255,.03)", padding: 14, color: "#cbd5e1" }}>{note}</div>)}</div>
                </div>
              </div>
            )}

            {activePage === "content" && (
              <div>
                <div style={{ marginBottom: 18, display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
                  <div><div style={{ fontSize: 30, fontWeight: 700 }}>Контент</div><div style={{ color: "#94a3b8", marginTop: 4 }}>Карточки и быстрая загрузка фото или видео прямо в систему</div></div>
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <button onClick={() => bulkAction("Массовый экспорт")} style={{ borderRadius: 16, border: "1px solid rgba(217,70,239,.2)", background: "rgba(217,70,239,.1)", color: "#f0abfc", padding: "12px 14px" }}>Выгрузить</button>
                    <button onClick={() => bulkAction("Массовый импорт")} style={{ borderRadius: 16, border: "1px solid rgba(34,211,238,.2)", background: "rgba(34,211,238,.1)", color: "#67e8f9", padding: "12px 14px" }}>Загрузить пакет</button>
                    <button onClick={() => setShowContentDrawer(true)} style={{ borderRadius: 16, background: "linear-gradient(90deg,#06b6d4,#3b82f6)", color: "white", padding: "12px 16px", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}><Plus size={16} /> Создать карточку</button>
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 16, marginBottom: 18 }}>
                  <MetricCard icon={FolderKanban} label="Всего карточек" value={content.length} caption="Полный каталог" />
                  <MetricCard icon={CheckCircle2} label="Опубликовано" value={content.filter((c) => c.status === "published").length} caption="В live-выдаче" />
                  <MetricCard icon={ImageIcon} label="Фото" value={content.filter((c) => c.type !== "Видео").length} caption="Картинки и постеры" />
                  <MetricCard icon={Video} label="Видео" value={content.filter((c) => c.type === "Видео").length} caption="Трейлеры и ролики" />
                </div>
                <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
                  <button style={{ borderRadius: 16, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.04)", padding: "12px 14px", color: "#cbd5e1" }}><span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}><Filter size={16} /> Фильтр</span></button>
                  {[
                    "Массовая публикация",
                    "Массовая архивация",
                    "Массовая выгрузка карточек",
                    "Массовая загрузка файлов",
                    "Аналитика за день",
                    "Аналитика за месяц",
                  ].map((label) => (
                    <button key={label} onClick={() => bulkAction(label)} style={{ borderRadius: 16, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.04)", color: "#cbd5e1", padding: "12px 14px" }}>{label}</button>
                  ))}
                </div>
                <div style={{ ...cardStyle(), overflow: "hidden" }}>
                  <table style={{ width: "100%" }}>
                    <thead><tr><th>Название</th><th>Тип</th><th>Код</th><th>Статус</th><th>Видимость</th><th>Автор</th><th>Обновлено</th><th>Действия</th></tr></thead>
                    <tbody>
                      {filteredContent.map((item) => (
                        <tr key={item.id}>
                          <td>
                            <div style={{ fontWeight: 600, color: "white" }}>{item.title}</div>
                            <div style={{ marginTop: 6, display: "flex", gap: 6, flexWrap: "wrap", fontSize: 11, color: "#94a3b8" }}>
                              <span>{item.cover}</span>
                              {item.tags.map((tag) => <span key={tag} style={{ borderRadius: 999, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.03)", padding: "2px 8px" }}>#{tag}</span>)}
                            </div>
                          </td>
                          <td>{item.type}</td>
                          <td style={{ fontFamily: "monospace", color: "#67e8f9" }}>{item.code}</td>
                          <td><StatusBadge value={item.status} /></td>
                          <td><StatusBadge value={item.visibility} /></td>
                          <td>{item.author}</td>
                          <td><div>{item.updated}</div><div style={{ fontSize: 12, color: "#64748b" }}>{item.schedule}</div></td>
                          <td>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                              <button style={{ borderRadius: 14, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.04)", padding: 10, color: "#cbd5e1" }}><Pencil size={16} /></button>
                              <button onClick={() => togglePublish(item.id)} style={{ borderRadius: 14, border: "1px solid rgba(16,185,129,.2)", background: "rgba(16,185,129,.1)", padding: "8px 10px", color: "#86efac" }}>{item.status === "published" ? "Отключить" : "Publish"}</button>
                              <button onClick={() => toggleVisibility(item.id)} style={{ borderRadius: 14, border: "1px solid rgba(245,158,11,.2)", background: "rgba(245,158,11,.1)", padding: "8px 10px", color: "#fcd34d" }}>Скрыть</button>
                              <button onClick={() => toggleArchive(item.id)} style={{ borderRadius: 14, border: "1px solid rgba(139,92,246,.2)", background: "rgba(139,92,246,.1)", padding: "8px 10px", color: "#c4b5fd" }}>Архив</button>
                              <button onClick={() => removeContent(item.id)} style={{ borderRadius: 14, border: "1px solid rgba(244,63,94,.2)", background: "rgba(244,63,94,.1)", padding: 10, color: "#fda4af" }}><Trash2 size={16} /></button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activePage === "media" && (
              <div>
                <div style={{ marginBottom: 18 }}><div style={{ fontSize: 30, fontWeight: 700 }}>Медиатека</div><div style={{ color: "#94a3b8", marginTop: 4 }}>Изображения, видео, баннеры и исходники</div></div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 16 }}>
                  <MetricCard icon={ImageIcon} label="Постеры" value="248" caption="Обложки карточек" />
                  <MetricCard icon={Video} label="Видео" value="71" caption="Трейлеры и клипы" />
                  <MetricCard icon={RefreshCw} label="Очередь" value="12" caption="В обработке" />
                  <MetricCard icon={Database} label="Хранилище" value="CDN" caption="Файлы и ссылки" />
                </div>
              </div>
            )}

            {activePage === "users" && (
              <div>
                <div style={{ marginBottom: 18, display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center" }}>
                  <div><div style={{ fontSize: 30, fontWeight: 700 }}>Команда</div><div style={{ color: "#94a3b8", marginTop: 4 }}>Создание сотрудников и сброс пароля</div></div>
                  <button onClick={() => setShowUserDrawer(true)} style={{ borderRadius: 16, background: "linear-gradient(90deg,#06b6d4,#3b82f6)", color: "white", padding: "12px 16px", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}><Plus size={16} /> Добавить сотрудника</button>
                </div>
                <div style={{ ...cardStyle(), overflow: "hidden" }}>
                  <table style={{ width: "100%" }}>
                    <thead><tr><th>Сотрудник</th><th>Роль</th><th>Статус</th><th>2FA</th><th>Доступы</th><th>Действия</th></tr></thead>
                    <tbody>
                      {filteredUsers.map((user) => (
                        <tr key={user.id}>
                          <td><div style={{ fontWeight: 600 }}>{user.name}</div><div style={{ color: "#94a3b8", fontSize: 14 }}>@{user.username} · {user.email}</div></td>
                          <td>{user.role}</td>
                          <td><StatusBadge value={user.status} /></td>
                          <td>{user.twoFA ? <CheckCircle2 size={16} color="#86efac" /> : <XCircle size={16} color="#64748b" />}</td>
                          <td style={{ color: "#94a3b8", fontSize: 14 }}>{user.directAccess.join(", ") || "—"}</td>
                          <td><button onClick={() => notify(`Пароль для ${user.username} сброшен.`)} style={{ borderRadius: 14, border: "1px solid rgba(217,70,239,.2)", background: "rgba(217,70,239,.1)", color: "#f0abfc", padding: "8px 10px" }}>Сбросить пароль</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activePage === "roles" && (
              <div>
                <div style={{ marginBottom: 18, display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center" }}>
                  <div><div style={{ fontSize: 30, fontWeight: 700 }}>Роли и доступы</div><div style={{ color: "#94a3b8", marginTop: 4 }}>Гибкая RBAC-система</div></div>
                  <button onClick={() => setShowRoleDrawer(true)} style={{ borderRadius: 16, background: "linear-gradient(90deg,#8b5cf6,#d946ef)", color: "white", padding: "12px 16px", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}><Plus size={16} /> Создать роль</button>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 16 }}>
                  {roles.map((role) => (
                    <div key={role.id} style={cardStyle()}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                        <div>
                          <div style={{ display: "inline-flex", borderRadius: 999, background: role.color, padding: "6px 12px", fontSize: 14, fontWeight: 700 }}>{role.name}</div>
                          <div style={{ marginTop: 10, color: "#94a3b8", fontSize: 14 }}>{role.permissions.length} разрешений</div>
                        </div>
                        <button style={{ borderRadius: 16, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.04)", padding: 12, color: "#cbd5e1" }}><Pencil size={16} /></button>
                      </div>
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 16 }}>
                        {role.permissions.map((permission) => <span key={permission} style={{ borderRadius: 999, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.04)", padding: "6px 10px", fontSize: 12, color: "#cbd5e1" }}>{permission}</span>)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activePage === "security" && (
              <div>
                <div style={{ marginBottom: 18 }}><div style={{ fontSize: 30, fontWeight: 700 }}>Безопасность</div><div style={{ color: "#94a3b8", marginTop: 4 }}>Вход, забыли пароль, аудит и доступы</div></div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 16 }}>
                  <div style={cardStyle()}>
                    <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 12 }}>Состояние защиты</div>
                    <div style={{ display: "grid", gap: 12 }}>
                      <div style={{ borderRadius: 16, border: "1px solid rgba(255,255,255,.08)", background: "rgba(255,255,255,.03)", padding: 14 }}>2FA для Owner и Admin</div>
                      <div style={{ borderRadius: 16, border: "1px solid rgba(255,255,255,.08)", background: "rgba(255,255,255,.03)", padding: 14 }}>Сброс пароля по email</div>
                      <div style={{ borderRadius: 16, border: "1px solid rgba(255,255,255,.08)", background: "rgba(255,255,255,.03)", padding: 14 }}>Ручной reset пароля руководителем</div>
                    </div>
                  </div>
                  <div style={cardStyle()}>
                    <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 12 }}>Последние события</div>
                    <div style={{ display: "grid", gap: 10 }}>
                      {["owner вошёл в систему", "creator.marina запросил восстановление", "operator.ilya подтвердил 2FA"].map((item, i) => <div key={i} style={{ borderRadius: 16, border: "1px solid rgba(255,255,255,.08)", background: "rgba(255,255,255,.03)", padding: 14 }}>{item}</div>)}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activePage === "integrations" && (
              <div>
                <div style={{ marginBottom: 18, display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center" }}>
                  <div><div style={{ fontSize: 30, fontWeight: 700 }}>Интеграции</div><div style={{ color: "#94a3b8", marginTop: 4 }}>Единая синхронизация Telegram / VK</div></div>
                  <button onClick={() => setShowIntegrationDrawer(true)} style={{ borderRadius: 16, background: "linear-gradient(90deg,#06b6d4,#8b5cf6)", color: "white", padding: "12px 16px", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}><Plus size={16} /> Добавить интеграцию</button>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 16 }}>
                  {integrations.map((item) => (
                    <div key={item.id} style={cardStyle()}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                        <div><div style={{ fontSize: 22, fontWeight: 700 }}>{item.name}</div><div style={{ marginTop: 4, color: "#94a3b8", fontSize: 14 }}>{item.handle}</div></div>
                        <StatusBadge value={item.state} />
                      </div>
                      <div style={{ marginTop: 12, color: "#94a3b8", fontSize: 14 }}>{item.description}</div>
                      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 16 }}>
                        <button onClick={() => toggleSync(item.id)} style={{ borderRadius: 14, border: "1px solid rgba(34,211,238,.2)", background: "rgba(34,211,238,.1)", color: "#67e8f9", padding: "8px 10px" }}>{item.sync ? "Отключить sync" : "Включить sync"}</button>
                        <button onClick={() => notify(`Интеграция ${item.name} временно отключена.`)} style={{ borderRadius: 14, border: "1px solid rgba(244,63,94,.2)", background: "rgba(244,63,94,.1)", color: "#fda4af", padding: "8px 10px" }}>Временно отключить</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activePage === "analytics" && (
              <div>
                <div style={{ marginBottom: 18 }}><div style={{ fontSize: 30, fontWeight: 700 }}>Аналитика</div><div style={{ color: "#94a3b8", marginTop: 4 }}>Просмотры, выдачи и публикации</div></div>
                <div style={{ display: "grid", gridTemplateColumns: "1.25fr .75fr", gap: 16 }}>
                  <div style={cardStyle()}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}><div><div style={{ fontSize: 20, fontWeight: 700 }}>Динамика выдач</div><div style={{ color: "#94a3b8", marginTop: 4, fontSize: 14 }}>Последние 30 дней</div></div></div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(12, minmax(0,1fr))", gap: 8, height: 240, alignItems: "end", borderRadius: 24, border: "1px solid rgba(255,255,255,.08)", background: "rgba(2,6,23,.4)", padding: 16 }}>
                      {[42,58,71,65,81,92,76,98,88,100,96,120].map((v, i) => <div key={i} style={{ display: "flex", flexDirection: "column", justifyContent: "end", gap: 8, height: "100%" }}><div style={{ height: `${v}%`, borderRadius: "16px 16px 0 0", background: "linear-gradient(to top,#06b6d4,#8b5cf6)" }} /><div style={{ textAlign: "center", fontSize: 12, color: "#64748b" }}>{i + 1}</div></div>)}
                    </div>
                  </div>
                  <div style={{ display: "grid", gap: 16 }}>
                    <MetricCard icon={Activity} label="Выдачи по кодам" value="12 480" caption="За последние 30 дней" />
                    <MetricCard icon={Globe} label="Интеграции online" value={integrations.length} caption="Все каналы в боевом режиме" />
                    <MetricCard icon={RefreshCw} label="Экспорт отчётов" value="CSV" caption="День / неделя / месяц" />
                  </div>
                </div>
              </div>
            )}

            {activePage === "settings" && (
              <div>
                <div style={{ marginBottom: 18 }}><div style={{ fontSize: 30, fontWeight: 700 }}>Настройки</div><div style={{ color: "#94a3b8", marginTop: 4 }}>Системные параметры панели</div></div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 16 }}>
                  <div style={cardStyle()}><Field label="Название панели" value="Anime Platform" onChange={() => {}} /></div>
                  <div style={cardStyle()}><div style={{ fontSize: 22, fontWeight: 700 }}>Ядро</div><div style={{ marginTop: 10, color: "#94a3b8" }}>FastAPI + PostgreSQL + JWT + роли + права</div></div>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>

      <Drawer open={showForgot} onClose={() => setShowForgot(false)} title="Забыли пароль?">
        <div style={{ display: "grid", gap: 16 }}>
          <Field label="Email администратора" value={forgotEmail} onChange={setForgotEmail} placeholder="owner@example.com" />
          <button onClick={() => { setShowForgot(false); notify(`Ссылка отправлена на ${forgotEmail}`); }} style={{ borderRadius: 16, background: "linear-gradient(90deg,#06b6d4,#3b82f6)", color: "white", padding: "12px 16px", fontWeight: 700 }}>Отправить ссылку</button>
        </div>
      </Drawer>

      <Drawer open={showUserDrawer} onClose={() => setShowUserDrawer(false)} title="Новый сотрудник">
        <div style={{ display: "grid", gap: 16 }}>
          <Field label="Имя" value={newUser.name} onChange={(v) => setNewUser((s) => ({ ...s, name: v }))} placeholder="Марина Контент" />
          <Field label="Логин" value={newUser.username} onChange={(v) => setNewUser((s) => ({ ...s, username: v }))} placeholder="creator.marina" />
          <Field label="Email" value={newUser.email} onChange={(v) => setNewUser((s) => ({ ...s, email: v }))} placeholder="creator@example.com" />
          <Field label="Роль" value={newUser.role} onChange={(v) => setNewUser((s) => ({ ...s, role: v }))} placeholder="Creator" />
          <button onClick={addUser} style={{ borderRadius: 16, background: "linear-gradient(90deg,#06b6d4,#3b82f6)", color: "white", padding: "12px 16px", fontWeight: 700 }}>Создать сотрудника</button>
        </div>
      </Drawer>

      <Drawer open={showRoleDrawer} onClose={() => setShowRoleDrawer(false)} title="Новая роль">
        <div style={{ display: "grid", gap: 16 }}>
          <Field label="Название роли" value={newRoleName} onChange={setNewRoleName} placeholder="Creator Plus" />
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>{["content.view","content.create","content.update","media.upload"].map((permission) => <span key={permission} style={{ borderRadius: 999, border: "1px solid rgba(34,211,238,.15)", background: "rgba(34,211,238,.1)", color: "#67e8f9", padding: "6px 10px", fontSize: 12 }}>{permission}</span>)}</div>
          <button onClick={addRole} style={{ borderRadius: 16, background: "linear-gradient(90deg,#8b5cf6,#d946ef)", color: "white", padding: "12px 16px", fontWeight: 700 }}>Создать роль</button>
        </div>
      </Drawer>

      <Drawer open={showContentDrawer} onClose={() => setShowContentDrawer(false)} title="Создать карточку">
        <div style={{ display: "grid", gap: 16 }}>
          <Field label="Название" value={newContent.title} onChange={(v) => setNewContent((s) => ({ ...s, title: v }))} placeholder="Название карточки" />
          <label>
            <div style={{ marginBottom: 8, fontSize: 14, color: "#cbd5e1" }}>Описание</div>
            <textarea value={newContent.description} onChange={(e) => setNewContent((s) => ({ ...s, description: e.target.value }))} rows={5} placeholder="Описание карточки" style={{ width: "100%", borderRadius: 18, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.05)", color: "white", padding: "14px 16px", outline: "none" }} />
          </label>
          <Field label="Теги через запятую" value={newContent.tags} onChange={(v) => setNewContent((s) => ({ ...s, tags: v }))} placeholder="аниме, хит, новинка" />
          <label>
            <div style={{ marginBottom: 8, fontSize: 14, color: "#cbd5e1" }}>Тип файла</div>
            <select value={newContent.mediaType} onChange={(e) => setNewContent((s) => ({ ...s, mediaType: e.target.value }))} style={{ width: "100%", borderRadius: 18, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.05)", color: "white", padding: "14px 16px", outline: "none" }}>
              <option value="image">Фото</option>
              <option value="video">Видео</option>
            </select>
          </label>
          <label>
            <div style={{ marginBottom: 8, fontSize: 14, color: "#cbd5e1" }}>Загрузить файл</div>
            <input type="file" accept={newContent.mediaType === "video" ? "video/*" : "image/*"} onChange={(e) => setNewContent((s) => ({ ...s, mediaFileName: e.target.files?.[0]?.name || "" }))} style={{ width: "100%", borderRadius: 18, border: "1px dashed rgba(255,255,255,.15)", background: "rgba(255,255,255,.03)", color: "#cbd5e1", padding: "14px 16px" }} />
            <div style={{ marginTop: 8, fontSize: 12, color: "#64748b" }}>{newContent.mediaFileName ? `Выбран файл: ${newContent.mediaFileName}` : "Файл ещё не выбран"}</div>
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 16 }}>
            <label>
              <div style={{ marginBottom: 8, fontSize: 14, color: "#cbd5e1" }}>Статус</div>
              <select value={newContent.status} onChange={(e) => setNewContent((s) => ({ ...s, status: e.target.value }))} style={{ width: "100%", borderRadius: 18, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.05)", color: "white", padding: "14px 16px", outline: "none" }}>
                <option value="draft">draft</option>
                <option value="published">published</option>
                <option value="archived">archived</option>
              </select>
            </label>
            <label>
              <div style={{ marginBottom: 8, fontSize: 14, color: "#cbd5e1" }}>Видимость</div>
              <select value={newContent.visibility} onChange={(e) => setNewContent((s) => ({ ...s, visibility: e.target.value }))} style={{ width: "100%", borderRadius: 18, border: "1px solid rgba(255,255,255,.1)", background: "rgba(255,255,255,.05)", color: "white", padding: "14px 16px", outline: "none" }}>
                <option value="public">public</option>
                <option value="hidden">hidden</option>
                <option value="private">private</option>
              </select>
            </label>
          </div>
          <button onClick={addContentCard} style={{ borderRadius: 16, background: "linear-gradient(90deg,#06b6d4,#3b82f6)", color: "white", padding: "12px 16px", fontWeight: 700 }}>Сохранить карточку</button>
        </div>
      </Drawer>

      <Drawer open={showIntegrationDrawer} onClose={() => setShowIntegrationDrawer(false)} title="Новая интеграция">
        <div style={{ display: "grid", gap: 16 }}>
          <Field label="Название" value={newIntegration.name} onChange={(v) => setNewIntegration((s) => ({ ...s, name: v }))} placeholder="Telegram Bot 2" />
          <Field label="Handle / URL" value={newIntegration.handle} onChange={(v) => setNewIntegration((s) => ({ ...s, handle: v }))} placeholder="@new_release_bot" />
          <button onClick={addIntegration} style={{ borderRadius: 16, background: "linear-gradient(90deg,#06b6d4,#8b5cf6)", color: "white", padding: "12px 16px", fontWeight: 700 }}>Подключить интеграцию</button>
        </div>
      </Drawer>
    </div>
  );
}
