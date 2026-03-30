from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> AuditLog:
        entity = AuditLog(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def list_recent(self, limit: int = 200) -> list[AuditLog]:
        statement = select(AuditLog).options(joinedload(AuditLog.admin)).order_by(AuditLog.id.desc()).limit(limit)
        return list(self.session.scalars(statement).unique())

    def list_filtered(self, *, admin_id: int | None = None, action: str = '', date_from: str = '', date_to: str = '', sort: str = 'desc', limit: int = 500) -> list[AuditLog]:
        statement = select(AuditLog).options(joinedload(AuditLog.admin))
        if admin_id:
            statement = statement.where(AuditLog.admin_id == admin_id)
        if action:
            statement = statement.where(AuditLog.action == action)
        if date_from:
            statement = statement.where(AuditLog.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            end_dt = datetime.fromisoformat(date_to) + timedelta(days=1)
            statement = statement.where(AuditLog.created_at < end_dt)
        statement = statement.order_by(AuditLog.created_at.asc() if sort == 'asc' else AuditLog.created_at.desc()).limit(limit)
        return list(self.session.scalars(statement).unique())

    def list_actions(self) -> list[str]:
        rows = self.session.execute(select(AuditLog.action).distinct().order_by(AuditLog.action.asc())).all()
        return [row[0] for row in rows]

    def purge_older_than(self, days: int) -> int:
        if days <= 0:
            return 0
        threshold = datetime.utcnow() - timedelta(days=days)
        rows = self.session.query(AuditLog).filter(AuditLog.created_at < threshold).delete(synchronize_session=False)
        self.session.flush()
        return int(rows or 0)
