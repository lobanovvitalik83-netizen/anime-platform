from app.models.admin import Admin

PERMISSION_DEFINITIONS = [
    ("reports_view", "Просмотр репортов"),
    ("reports_reply", "Ответ на репорты"),
    ("settings_manage", "Настройки сайта"),
    ("analytics_view", "Просмотр аналитики"),
    ("analytics_export", "Экспорт аналитики"),
    ("import_export", "Импорт и экспорт данных"),
    ("editor_tools", "Инструменты редактора"),
    ("team_manage", "Управление персоналом"),
    ("messages_manage", "Сообщения и чаты"),
    ("media_manage", "Управление медиа"),
    ("codes_manage", "Управление кодами"),
    ("admin_actions_view", "Просмотр действий админов"),
    ("achievement_manage", "Ачивки и награды"),
]

ALL_PERMISSIONS = [code for code, _label in PERMISSION_DEFINITIONS]
PERMISSION_LABELS = {code: label for code, label in PERMISSION_DEFINITIONS}

DEFAULT_ROLE_PERMISSIONS = {
    "superadmin": set(ALL_PERMISSIONS),
    "assistant": set(ALL_PERMISSIONS) - {"team_manage"},
    "admin": {"reports_view", "reports_reply", "analytics_view", "analytics_export", "import_export", "editor_tools", "team_manage", "messages_manage", "media_manage", "codes_manage", "admin_actions_view", "achievement_manage"},
    "support": {"reports_view", "reports_reply", "messages_manage"},
    "editor": {"editor_tools", "messages_manage", "media_manage", "codes_manage"},
}

class PermissionService:
    def parse_permissions(self, raw: str | None) -> set[str]:
        if not raw:
            return set()
        return {item.strip() for item in raw.split(",") if item.strip()}

    def serialize_permissions(self, permissions) -> str:
        return ",".join(sorted({item.strip() for item in permissions if item and item.strip()}))

    def get_permissions(self, admin: Admin) -> set[str]:
        return set(DEFAULT_ROLE_PERMISSIONS.get(admin.role, set())) | self.parse_permissions(getattr(admin, "extra_permissions", None))

    def has_permission(self, admin: Admin | None, permission: str) -> bool:
        if not admin:
            return False
        return permission in self.get_permissions(admin)

    def label(self, permission: str) -> str:
        return PERMISSION_LABELS.get(permission, permission)
