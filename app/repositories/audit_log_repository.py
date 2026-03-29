from sqlalchemy import select
from sqlalchemy.orm import Session

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
        statement = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
        return list(self.session.scalars(statement))
