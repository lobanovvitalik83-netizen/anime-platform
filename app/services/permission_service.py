from app.models.admin import Admin

ALL_PERMISSIONS = [
    "reports_view",
    "reports_reply",
    "settings_manage",
    "analytics_view",
    "import_export",
    "editor_tools",
    "team_manage",
    "messages_manage",
]

DEFAULT_ROLE_PERMISSIONS = {
    "superadmin": set(ALL_PERMISSIONS),
    "admin": {"reports_view", "reports_reply", "analytics_view", "import_export", "editor_tools", "team_manage", "messages_manage"},
    "support": {"reports_view", "reports_reply", "messages_manage"},
    "editor": {"editor_tools", "messages_manage"},
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
