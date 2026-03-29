from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.repositories.admin_notification_repository import AdminNotificationRepository
from app.repositories.admin_repository import AdminRepository
from app.services.permission_service import PermissionService


class NotificationService:
    def __init__(self, session: Session):
        self.session = session
        self.notifications = AdminNotificationRepository(session)
        self.admins = AdminRepository(session)
        self.permissions = PermissionService()

    def notify_admin(self, admin_id: int, *, kind: str, title: str, body: str = "", link_url: str | None = None):
        self.notifications.create(
            admin_id=admin_id,
            kind=kind,
            title=title[:255],
            body=body[:2000] if body else None,
            link_url=link_url,
            is_read=False,
        )

    def notify_by_permission(self, permission: str, *, kind: str, title: str, body: str = "", link_url: str | None = None, exclude_admin_ids: set[int] | None = None):
        exclude_admin_ids = exclude_admin_ids or set()
        for admin in self.admins.list_active():
            if admin.id in exclude_admin_ids:
                continue
            if admin.role == "superadmin" or self.permissions.has_permission(admin, permission):
                self.notify_admin(admin.id, kind=kind, title=title, body=body, link_url=link_url)

    def list_for_admin(self, admin: Admin, *, only_unread: bool = False, limit: int = 200):
        return self.notifications.list_for_admin(admin.id, only_unread=only_unread, limit=limit)

    def unread_count(self, admin: Admin) -> int:
        return self.notifications.unread_count(admin.id)

    def mark_read(self, admin: Admin, notification_id: int):
        item = self.notifications.get_by_id(notification_id)
        if not item or item.admin_id != admin.id:
            return None
        return self.notifications.mark_read(item)
