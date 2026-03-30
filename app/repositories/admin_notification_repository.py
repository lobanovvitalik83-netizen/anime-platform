from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.admin_notification import AdminNotification


class AdminNotificationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> AdminNotification:
        entity = AdminNotification(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def get_by_id(self, notification_id: int) -> AdminNotification | None:
        stmt = select(AdminNotification).where(AdminNotification.id == notification_id).options(selectinload(AdminNotification.admin))
        return self.session.scalar(stmt)

    def list_for_admin(self, admin_id: int, *, only_unread: bool = False, limit: int = 200) -> list[AdminNotification]:
        stmt = select(AdminNotification).where(AdminNotification.admin_id == admin_id).order_by(AdminNotification.created_at.desc()).limit(limit).options(selectinload(AdminNotification.admin))
        if only_unread:
            stmt = stmt.where(AdminNotification.is_read == False)  # noqa: E712
        return list(self.session.scalars(stmt))

    def unread_count(self, admin_id: int) -> int:
        stmt = (
            select(func.count(AdminNotification.id))
            .where(AdminNotification.admin_id == admin_id, AdminNotification.is_read == False)  # noqa: E712
        )
        return int(self.session.scalar(stmt) or 0)

    def mark_read(self, entity: AdminNotification) -> AdminNotification:
        entity.is_read = True
        self.session.flush()
        return entity

    def purge_older_than(self, days: int) -> int:
        if days <= 0:
            return 0
        threshold = datetime.utcnow() - timedelta(days=days)
        rows = self.session.query(AdminNotification).filter(AdminNotification.created_at < threshold).delete(synchronize_session=False)
        self.session.flush()
        return int(rows or 0)
