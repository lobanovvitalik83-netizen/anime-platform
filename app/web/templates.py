from fastapi.templating import Jinja2Templates

from app.services.permission_service import PermissionService

templates = Jinja2Templates(directory="app/web/templates")

_perm = PermissionService()

def can_access(admin, permission: str) -> bool:
    if not admin:
        return False
    if admin.role == "superadmin":
        return True
    return _perm.has_permission(admin, permission)

def nav_sections(admin):
    if not admin:
        return []
    sections = []

    content_items = []
    if can_access(admin, "media_manage") or can_access(admin, "editor_tools"):
        content_items.append({"label": "Дашборд", "href": "/admin"})
        content_items.append({"label": "Медиа", "href": "/admin/media"})
        if can_access(admin, "media_manage") or can_access(admin, "editor_tools"):
            content_items.append({"label": "Создать карточку", "href": "/admin/card-builder"})
    if can_access(admin, "codes_manage") or admin.role == "superadmin":
        content_items.append({"label": "Коды", "href": "/admin/codes"})
        content_items.append({"label": "Lookup test", "href": "/admin/lookup-test"})
    if content_items:
        sections.append({"title": "Контент", "items": content_items})

    comm_items = []
    if can_access(admin, "messages_manage"):
        comm_items.append({"label": "Сообщения", "href": "/admin/chats-live"})
    if can_access(admin, "reports_view"):
        comm_items.append({"label": "Репорты", "href": "/admin/reports"})
    comm_items.append({"label": "Уведомления", "href": "/admin/notifications"})
    if comm_items:
        sections.append({"title": "Коммуникации", "items": comm_items})

    team_items = [{"label": "Сотрудники", "href": "/admin/people"}]
    if can_access(admin, "team_manage"):
        team_items.append({"label": "Персонал", "href": "/admin/team"})
    team_items.append({"label": "Ачивки", "href": "/admin/achievements"})
    sections.append({"title": "Команда", "items": team_items})

    control_items = []
    if can_access(admin, "analytics_view"):
        control_items.append({"label": "Аналитика", "href": "/admin/analytics"})
        control_items.append({"label": "Расширенная аналитика", "href": "/admin/analytics/advanced"})
    if can_access(admin, "admin_actions_view"):
        control_items.append({"label": "Действия админов", "href": "/admin/admin-actions"})
    if can_access(admin, "import_export"):
        control_items.append({"label": "Импорт/экспорт", "href": "/admin/import-export/advanced"})
    if control_items:
        sections.append({"title": "Контроль", "items": control_items})

    account_items = [{"label": "Профиль", "href": "/admin/profile"}]
    if can_access(admin, "settings_manage"):
        account_items.append({"label": "Настройки", "href": "/admin/settings/advanced"})
    if admin.role == "superadmin":
        account_items.append({"label": "API docs", "href": "/admin/api-docs"})
    account_items.append({"label": "Выход", "href": "/admin/logout"})
    sections.append({"title": "Аккаунт", "items": account_items})

    return sections

templates.env.globals["can_access"] = can_access
templates.env.globals["nav_sections"] = nav_sections
