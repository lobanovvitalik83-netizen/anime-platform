import re
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.admin_repository import AdminRepository
from app.services.audit_service import AuditService

_slug_re = re.compile(r"[^a-z0-9]+")

class AchievementService:
    def __init__(self, session: Session):
        self.session = session
        self.achievements = AchievementRepository(session)
        self.admins = AdminRepository(session)
        self.audit = AuditService(session)

    def _slugify(self, text: str) -> str:
        slug = _slug_re.sub("-", text.strip().lower()).strip("-")
        return slug[:140] or "achievement"

    def list_achievements(self):
        return self.achievements.list_all()

    def list_active_achievements(self):
        return self.achievements.list_active()

    def list_admin_achievements(self, admin_id: int):
        return self.achievements.list_admin_grants(admin_id)

    def get_achievement(self, achievement_id: int):
        item = self.achievements.get_by_id(achievement_id)
        if not item:
            raise NotFoundError("Ачивка не найдена.")
        return item

    def create_achievement(self, actor_id: int, *, title: str, description: str | None, icon_emoji: str | None, color: str | None, is_active: bool):
        title = (title or "").strip()
        if not title:
            raise ValidationError("Название ачивки обязательно.")
        slug = self._slugify(title)
        if self.achievements.get_by_slug(slug):
            raise ConflictError("Ачивка с таким slug уже существует.")
        item = self.achievements.create(
            title=title,
            slug=slug,
            description=(description or "").strip() or None,
            icon_emoji=(icon_emoji or "").strip() or "🏆",
            color=(color or "").strip() or "#4f7cff",
            is_active=is_active,
        )
        self.audit.log(actor_id, "create_achievement", "achievement", str(item.id), {"title": item.title})
        self.session.commit()
        return item

    def update_achievement(self, actor_id: int, achievement_id: int, *, title: str, description: str | None, icon_emoji: str | None, color: str | None, is_active: bool):
        item = self.get_achievement(achievement_id)
        title = (title or "").strip()
        if not title:
            raise ValidationError("Название ачивки обязательно.")
        slug = self._slugify(title)
        existing = self.achievements.get_by_slug(slug)
        if existing and existing.id != item.id:
            raise ConflictError("Ачивка с таким slug уже существует.")
        item = self.achievements.update(
            item,
            title=title,
            slug=slug,
            description=(description or "").strip() or None,
            icon_emoji=(icon_emoji or "").strip() or "🏆",
            color=(color or "").strip() or "#4f7cff",
            is_active=is_active,
        )
        self.audit.log(actor_id, "update_achievement", "achievement", str(item.id), {"title": item.title})
        self.session.commit()
        return item

    def delete_achievement(self, actor_id: int, achievement_id: int):
        item = self.get_achievement(achievement_id)
        self.audit.log(actor_id, "delete_achievement", "achievement", str(item.id), {"title": item.title})
        self.achievements.delete(item)
        self.session.commit()

    def grant_to_admin(self, actor_id: int, *, target_admin_id: int, achievement_id: int, note: str | None):
        target = self.admins.get_by_id(target_admin_id)
        if not target:
            raise NotFoundError("Сотрудник не найден.")
        achievement = self.get_achievement(achievement_id)
        if self.achievements.has_grant(target_admin_id, achievement_id):
            raise ConflictError("Эта ачивка уже выдана пользователю.")
        grant = self.achievements.grant(
            admin_id=target_admin_id,
            achievement_id=achievement_id,
            issued_by_admin_id=actor_id,
            note=(note or "").strip() or None,
        )
        self.audit.log(actor_id, "grant_achievement", "admin_achievement", str(grant.id), {"achievement": achievement.title, "target_admin_id": target_admin_id})
        self.session.commit()
        return grant

    def revoke_from_admin(self, actor_id: int, grant_id: int):
        grants = self.session.get(__import__("app.models.admin_achievement", fromlist=["AdminAchievement"]).AdminAchievement, grant_id)
        if not grants:
            raise NotFoundError("Выдача не найдена.")
        self.audit.log(actor_id, "revoke_achievement", "admin_achievement", str(grants.id), {"target_admin_id": grants.admin_id})
        self.achievements.revoke(grants)
        self.session.commit()
