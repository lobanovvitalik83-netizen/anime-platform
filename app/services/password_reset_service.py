from datetime import datetime, timedelta
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import hash_password
from app.models.password_reset_token import PasswordResetToken
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService


class PasswordResetService:
    def __init__(self, session: Session):
        self.session = session
        self.audit = AuditService(session)
        self.auth = AuthService(session)

    def create_reset_link(self, actor, admin_id: int, public_base_url: str) -> tuple[str, PasswordResetToken]:
        target = self.auth.get_manageable_admin(actor, admin_id)
        token = secrets.token_urlsafe(32)
        entity = PasswordResetToken(
            admin_id=target.id,
            token=token,
            created_by_admin_id=actor.id,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_used=False,
        )
        self.session.add(entity)
        self.session.flush()
        self.audit.log(actor.id, "create_reset_link", "admin", str(target.id), {"token_id": entity.id})
        self.session.commit()
        base = public_base_url.rstrip("/")
        return f"{base}/admin/reset-password/{token}", entity

    def get_valid_token(self, token: str) -> PasswordResetToken:
        entity = self.session.scalar(select(PasswordResetToken).where(PasswordResetToken.token == token))
        if not entity:
            raise NotFoundError("Ссылка сброса пароля не найдена.")
        if entity.is_used:
            raise ValidationError("Ссылка уже использована.")
        if entity.expires_at < datetime.utcnow():
            raise ValidationError("Срок действия ссылки истёк.")
        return entity

    def consume(self, token: str, new_password: str) -> None:
        entity = self.get_valid_token(token)
        new_password = (new_password or "").strip()
        if len(new_password) < 8:
            raise ValidationError("Пароль должен быть не короче 8 символов.")
        entity.admin.password_hash = hash_password(new_password)
        entity.is_used = True
        entity.used_at = datetime.utcnow()
        self.session.flush()
        self.audit.log(entity.admin_id, "reset_password_by_link", "admin", str(entity.admin_id), {"token_id": entity.id})
        self.session.commit()
