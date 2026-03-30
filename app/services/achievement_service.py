import re
import secrets
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.repositories.admin_achievement_repository import AdminAchievementRepository
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.admin_repository import AdminRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class AchievementService:
    def __init__(self, session: Session):
        self.session = session
        self.achievements = AchievementRepository(session)
        self.grants = AdminAchievementRepository(session)
        self.admins = AdminRepository(session)
        self.audit = AuditService(session)
        self.notifications = NotificationService(session)

    def list_achievements(self, *, active_only: bool = False):
        return self.achievements.list_all(active_only=active_only)

    def get_achievement(self, achievement_id: int):
        item = self.achievements.get_by_id(achievement_id)
        if not item:
            raise NotFoundError('Ачивка не найдена.')
        return item

    def list_admin_achievements(self, admin_id: int):
        return self.grants.list_for_admin(admin_id)

    def save_achievement_icon(self, *, file_bytes: bytes, file_name: str, content_type: str | None) -> str:
        if not file_bytes:
            raise ValidationError('Файл ачивки пустой.')
        if len(file_bytes) > settings.max_achievement_icon_size_bytes:
            raise ValidationError('Иконка ачивки слишком большая.')
        if content_type and content_type.lower() not in settings.allowed_image_mime:
            raise ValidationError('Разрешены только изображения для иконки ачивки.')
        suffix = Path(file_name or 'icon.png').suffix.lower() or '.png'
        target_dir = settings.achievement_upload_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = f'ach_{secrets.token_hex(12)}{suffix}'
        target_path = target_dir / filename
        target_path.write_bytes(file_bytes)
        return f'/uploads/achievements/{filename}'

    def create_achievement(self, actor_id: int, payload: dict):
        title = (payload.get('title') or '').strip()
        if not title:
            raise ValidationError('Название ачивки обязательно.')
        slug = (payload.get('slug') or '').strip().lower()
        if not slug:
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or f'achievement-{title[:16].lower()}'
        if self.achievements.get_by_slug(slug):
            raise ConflictError('Slug ачивки уже существует.')
        item = self.achievements.create(
            slug=slug,
            title=title,
            description=(payload.get('description') or '').strip() or None,
            icon_url=(payload.get('icon_url') or '').strip() or None,
            is_active=bool(payload.get('is_active', True)),
        )
        self.audit.log(actor_id, 'create_achievement', 'achievement', str(item.id), {'title': item.title, 'slug': item.slug})
        self.session.commit()
        return item

    def update_achievement(self, actor_id: int, achievement_id: int, payload: dict):
        item = self.get_achievement(achievement_id)
        title = (payload.get('title') or '').strip()
        if not title:
            raise ValidationError('Название ачивки обязательно.')
        slug = (payload.get('slug') or '').strip().lower()
        if not slug:
            slug = item.slug
        existing = self.achievements.get_by_slug(slug)
        if existing and existing.id != item.id:
            raise ConflictError('Slug ачивки уже существует.')
        item = self.achievements.update(item, slug=slug, title=title, description=(payload.get('description') or '').strip() or None, icon_url=(payload.get('icon_url') or '').strip() or None, is_active=bool(payload.get('is_active', True)))
        self.audit.log(actor_id, 'update_achievement', 'achievement', str(item.id), {'title': item.title, 'slug': item.slug})
        self.session.commit()
        return item

    def delete_achievement(self, actor_id: int, achievement_id: int):
        item = self.get_achievement(achievement_id)
        self.audit.log(actor_id, 'delete_achievement', 'achievement', str(item.id), {'title': item.title})
        self.achievements.delete(item)
        self.session.commit()

    def grant_achievement(self, actor_id: int, admin_id: int, achievement_id: int, reason: str | None = None):
        admin = self.admins.get_by_id(admin_id)
        if not admin:
            raise NotFoundError('Сотрудник не найден.')
        achievement = self.get_achievement(achievement_id)
        if self.grants.find_existing(admin.id, achievement.id):
            raise ConflictError('Эта ачивка уже выдана сотруднику.')
        grant = self.grants.create(admin_id=admin.id, achievement_id=achievement.id, granted_by_admin_id=actor_id, grant_reason=(reason or '').strip() or None, display_order=0)
        self.audit.log(actor_id, 'grant_achievement', 'admin_achievement', str(grant.id), {'admin_id': admin.id, 'achievement_id': achievement.id})
        self.notifications.notify_admin(admin.id, kind='achievement', title=f'Новая ачивка: {achievement.title}', body=reason or 'Тебе выдали новую ачивку.', link_url='/admin/profile')
        self.session.commit()
        return grant

    def revoke_grant(self, actor_id: int, grant_id: int):
        grant = self.grants.get_by_id(grant_id)
        if not grant:
            raise NotFoundError('Выдача ачивки не найдена.')
        self.audit.log(actor_id, 'revoke_achievement', 'admin_achievement', str(grant.id), {'admin_id': grant.admin_id, 'achievement_id': grant.achievement_id})
        self.grants.delete(grant)
        self.session.commit()
