from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.admin import Admin
from app.repositories.achievement_repository import AchievementRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class AchievementService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = AchievementRepository(session)
        self.audit = AuditService(session)
        self.notifications = NotificationService(session)

    def list_achievements(self):
        return self.repo.list_achievements()

    def list_active_achievements(self):
        return self.repo.list_active_achievements()

    def get_achievement(self, achievement_id: int):
        item = self.repo.get_achievement(achievement_id)
        if not item:
            raise NotFoundError("Ачивка не найдена.")
        return item

    def create_achievement(self, actor: Admin, *, title: str, description: str | None, icon: str | None, color: str | None, is_active: bool):
        title = (title or "").strip()
        if not title:
            raise ValidationError("Название ачивки обязательно.")
        if self.repo.get_achievement_by_title(title):
            raise ConflictError("Ачивка с таким названием уже существует.")
        item = self.repo.create_achievement(
            title=title,
            description=(description or "").strip() or None,
            icon=(icon or "").strip() or "🏆",
            color=(color or "").strip() or "#4f7cff",
            is_active=is_active,
            created_by_admin_id=actor.id,
        )
        self.audit.log(actor.id, "create_achievement", "achievement", str(item.id), {"title": item.title})
        self.session.commit()
        return item

    def update_achievement(self, actor: Admin, achievement_id: int, *, title: str, description: str | None, icon: str | None, color: str | None, is_active: bool):
        item = self.get_achievement(achievement_id)
        title = (title or "").strip()
        if not title:
            raise ValidationError("Название ачивки обязательно.")
        existing = self.repo.get_achievement_by_title(title)
        if existing and existing.id != item.id:
            raise ConflictError("Ачивка с таким названием уже существует.")
        item = self.repo.update_achievement(
            item,
            title=title,
            description=(description or "").strip() or None,
            icon=(icon or "").strip() or "🏆",
            color=(color or "").strip() or "#4f7cff",
            is_active=is_active,
        )
        self.audit.log(actor.id, "update_achievement", "achievement", str(item.id), {"title": item.title})
        self.session.commit()
        return item

    def delete_achievement(self, actor: Admin, achievement_id: int):
        item = self.get_achievement(achievement_id)
        self.audit.log(actor.id, "delete_achievement", "achievement", str(item.id), {"title": item.title})
        self.repo.delete_achievement(item)
        self.session.commit()

    def list_for_admin(self, admin_id: int):
        return self.repo.list_grants_for_admin(admin_id)

    def grant_to_admin(self, actor: Admin, *, target_admin: Admin, achievement_id: int, note: str | None):
        achievement = self.get_achievement(achievement_id)
        if not achievement.is_active:
            raise ValidationError("Нельзя выдать неактивную ачивку.")
        grant = self.repo.grant(
            admin_id=target_admin.id,
            achievement_id=achievement.id,
            granted_by_admin_id=actor.id,
            note=(note or "").strip() or None,
            status="granted",
        )
        self.audit.log(actor.id, "grant_achievement", "admin_achievement", str(grant.id), {"target_admin_id": target_admin.id, "achievement_id": achievement.id, "title": achievement.title})
        self.notifications.notify_admin(
            target_admin.id,
            kind="achievement",
            title=f"Тебе выдали ачивку: {achievement.title}",
            body=(note or "").strip() or "Новая ачивка появилась в твоём профиле.",
            link_url=f"/admin/profile",
        )
        self.session.commit()
        return grant

    def revoke_grant(self, actor: Admin, grant_id: int):
        grant = self.repo.get_grant(grant_id)
        if not grant:
            raise NotFoundError("Выданная ачивка не найдена.")
        self.audit.log(actor.id, "revoke_achievement", "admin_achievement", str(grant.id), {"target_admin_id": grant.admin_id, "achievement_id": grant.achievement_id})
        self.repo.delete_grant(grant)
        self.session.commit()
