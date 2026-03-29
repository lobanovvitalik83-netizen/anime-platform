import secrets
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.admin_achievement_repository import AdminAchievementRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class AchievementService:
    def __init__(self, session: Session):
        self.session = session
        self.achievements = AchievementRepository(session)
        self.grants = AdminAchievementRepository(session)
        self.audit = AuditService(session)
        self.notifications = NotificationService(session)

    def list_achievements(self):
        return self.achievements.list_all()

    def get_achievement(self, achievement_id: int):
        item = self.achievements.get_by_id(achievement_id)
        if not item:
            raise NotFoundError("Ачивка не найдена.")
        return item

    def list_admin_achievements(self, admin_id: int):
        return self.grants.list_for_admin(admin_id)

    def create_achievement(self, actor_id: int, *, title: str, description: str | None, image_url: str | None):
        title = (title or "").strip()
        if not title:
            raise ValidationError("Название ачивки обязательно.")
        item = self.achievements.create(
            title=title,
            description=(description or "").strip() or None,
            image_url=(image_url or "").strip() or None,
        )
        self.audit.log(actor_id, "create_achievement", "achievement", str(item.id), {"title": item.title})
        self.session.commit()
        return item

    def update_achievement(self, actor_id: int, achievement_id: int, *, title: str, description: str | None, image_url: str | None):
        item = self.get_achievement(achievement_id)
        title = (title or "").strip()
        if not title:
            raise ValidationError("Название ачивки обязательно.")
        item = self.achievements.update(
            item,
            title=title,
            description=(description or "").strip() or None,
            image_url=(image_url or "").strip() or None,
        )
        self.audit.log(actor_id, "update_achievement", "achievement", str(item.id), {"title": item.title})
        self.session.commit()
        return item

    def delete_achievement(self, actor_id: int, achievement_id: int):
        item = self.get_achievement(achievement_id)
        self.audit.log(actor_id, "delete_achievement", "achievement", str(item.id), {"title": item.title})
        self.achievements.delete(item)
        self.session.commit()

    def grant_achievement(self, actor, *, admin_id: int, achievement_id: int, note: str | None):
        achievement = self.get_achievement(achievement_id)
        existing = self.grants.get_for_admin_and_achievement(admin_id, achievement_id)
        if existing:
            raise ValidationError("Эта ачивка уже выдана сотруднику.")
        grant = self.grants.create(
            admin_id=admin_id,
            achievement_id=achievement_id,
            note=(note or "").strip() or None,
            awarded_by_admin_id=actor.id,
            awarded_by_name=actor.full_name or actor.username,
        )
        self.audit.log(actor.id, "grant_achievement", "admin_achievement", str(grant.id), {"admin_id": admin_id, "achievement": achievement.title})
        self.notifications.notify_admin(
            admin_id,
            kind="achievement",
            title=f"Новая ачивка: {achievement.title}",
            body=(note or "").strip() or f"Вам выдали ачивку «{achievement.title}».",
            link_url=f"/admin/profile",
        )
        self.session.commit()
        return grant

    def revoke_grant(self, actor_id: int, grant_id: int):
        grant = self.grants.get_by_id(grant_id)
        if not grant:
            raise NotFoundError("Выдача ачивки не найдена.")
        self.audit.log(actor_id, "revoke_achievement", "admin_achievement", str(grant.id), {"admin_id": grant.admin_id, "achievement_id": grant.achievement_id})
        self.grants.delete(grant)
        self.session.commit()

    def save_achievement_image(self, *, file_bytes: bytes, file_name: str) -> str:
        ext = Path(file_name).suffix.lower() or ".png"
        if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            raise ValidationError("Поддерживаются PNG, JPG, WEBP, GIF.")
        folder = settings.public_upload_dir / "achievements"
        folder.mkdir(parents=True, exist_ok=True)
        name = f"{secrets.token_hex(12)}{ext}"
        path = folder / name
        path.write_bytes(file_bytes)
        return f"/uploads/achievements/{name}"
