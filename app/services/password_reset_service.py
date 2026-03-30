from datetime import datetime, timedelta
import secrets

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import hash_password, hash_token
from app.models.admin import Admin
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService


class PasswordResetService:
    def __init__(self, session: Session):
        self.session = session
        self.tokens = PasswordResetTokenRepository(session)
        self.auth = AuthService(session)
        self.audit = AuditService(session)

    def create_reset_link(self, actor: Admin, target_admin_id: int) -> tuple[str, str]:
        target = self.auth.get_manageable_admin(actor, target_admin_id)
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_token(raw_token)
        expires_at = datetime.utcnow() + timedelta(hours=settings.password_reset_token_ttl_hours)
        self.tokens.create(
            token_hash=token_hash,
            target_admin_id=target.id,
            created_by_admin_id=actor.id,
            expires_at=expires_at,
            used_at=None,
        )
        self.audit.log(actor.id, 'create_password_reset_link', 'admin', str(target.id), {'username': target.username, 'expires_at': expires_at.isoformat()})
        self.session.commit()
        relative_url = f'/admin/reset-password/{raw_token}'
        full_url = f"{settings.public_base_url}{relative_url}" if settings.public_base_url else relative_url
        return full_url, relative_url

    def validate_token(self, raw_token: str):
        entity = self.tokens.get_by_token_hash(hash_token(raw_token))
        if not entity:
            raise ValidationError('Ссылка сброса недействительна.')
        if entity.used_at is not None:
            raise ValidationError('Эта ссылка уже использована.')
        if entity.expires_at <= datetime.utcnow():
            raise ValidationError('Срок действия ссылки истёк.')
        return entity

    def consume_token(self, raw_token: str, new_password: str) -> Admin:
        entity = self.validate_token(raw_token)
        new_password = (new_password or '').strip()
        if len(new_password) < 6:
            raise ValidationError('Новый пароль должен быть не короче 6 символов.')
        target = entity.target_admin
        if target is None:
            raise NotFoundError('Пользователь не найден.')
        self.auth.admins.update(target, password_hash=hash_password(new_password))
        self.tokens.mark_used(entity)
        self.audit.log(entity.created_by_admin_id or target.id, 'consume_password_reset_link', 'admin', str(target.id), {'username': target.username})
        self.session.commit()
        return target
