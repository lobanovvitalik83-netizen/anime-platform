import json
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    def __init__(self, session: Session):
        self.repository = AuditLogRepository(session)

    def log(
        self,
        admin_id: int | None,
        action: str,
        entity_type: str,
        entity_id: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.repository.create(
            admin_id=admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_json=json.dumps(payload or {}, ensure_ascii=False),
        )
