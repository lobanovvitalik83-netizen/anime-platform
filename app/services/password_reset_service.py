from datetime import datetime, timedelta
import hashlib
import secrets

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import hash_password
from app.models.admin import Admin
from app.repositories.admin_repository import AdminRepository
from app.repositories.password_reset_repository import PasswordResetTokenRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class PasswordResetService:
    def __init__(self, session: Session):
        self.session = session
        self.admins = AdminRepository(session)
        self.tokens = PasswordResetTokenRepository(session)
        self.audit = AuditService(session)
        self.notifications = NotificationService(session)

    @staticmethod
    def _hash(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    def create_reset_link(self, actor: Admin, target_admin_id: int, ttl_minutes: int = 60) -> str:
        target = self.admins.get_by_id(target_admin_id)
        if not target:
            raise NotFoundError('Пользователь не найден.')
        raw_token = secrets.token_urlsafe(32)
        entity = self.tokens.create(
            admin_id=target.id,
            created_by_admin_id=actor.id,
            token_hash=self._hash(raw_token),
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
            used_at=None,
        )
        self.audit.log(actor.id, 'create_password_reset_link', 'admin', str(target.id), {'token_id': entity.id})
        self.session.commit()
        base = settings.public_base_url or ''
        path = f'/admin/reset-password/{raw_token}'
        return f'{base}{path}' if base else path

    def validate_token(self, raw_token: str):
        token = self.tokens.get_by_hash(self._hash(raw_token))
        if not token:
            raise ValidationError('Ссылка сброса пароля не найдена.')
        if token.used_at is not None:
            raise ValidationError('Эта ссылка уже была использована.')
        if token.expires_at < datetime.utcnow():
            raise ValidationError('Срок действия ссылки истёк.')
        if not token.admin or not token.admin.is_active:
            raise ValidationError('Пользователь для сброса пароля недоступен.')
        return token

    def reset_by_token(self, raw_token: str, new_password: str) -> Admin:
        token = self.validate_token(raw_token)
        new_password = (new_password or '').strip()
        if len(new_password) < 6:
            raise ValidationError('Пароль должен быть не короче 6 символов.')
        admin = token.admin
        admin.password_hash = hash_password(new_password)
        self.tokens.mark_used(token)
        self.audit.log(admin.id, 'password_reset_by_link', 'admin', str(admin.id), {'token_id': token.id})
        self.notifications.notify_admin(
            admin_id=admin.id,
            kind='password_reset_done',
            title='Пароль обновлён',
            body='Для твоего аккаунта был установлен новый пароль через ссылку сброса.',
            link_url='/admin/profile',
        )
        self.session.commit()
        return admin
