from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.admin import Admin
from app.repositories.achievement_repository import AchievementRepository, AdminAchievementRepository
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

    def list_achievements(self):
        return self.achievements.list_all()

    def list_active_achievements(self):
        return self.achievements.list_active()

    def get_achievement(self, achievement_id: int):
        item = self.achievements.get_by_id(achievement_id)
        if not item:
            raise NotFoundError("Ачивка не найдена.")
        return item

    def list_for_admin(self, admin_id: int):
        return self.grants.list_for_admin(admin_id)

    def create_achievement(self, actor: Admin, payload: dict):
        name = (payload.get("name") or "").strip()
        if not name:
            raise ValidationError("Название ачивки обязательно.")
        if self.achievements.get_by_name(name):
            raise ConflictError("Ачивка с таким названием уже существует.")
        item = self.achievements.create(
            name=name,
            description=(payload.get("description") or "").strip() or None,
            icon=(payload.get("icon") or "🏆").strip()[:16],
            color=(payload.get("color") or "#4c8bf5").strip()[:30],
            is_active=bool(payload.get("is_active", True)),
        )
        self.audit.log(actor.id, "create_achievement", "achievement", str(item.id), {"name": item.name})
        self.session.commit()
        return item

    def update_achievement(self, actor: Admin, achievement_id: int, payload: dict):
        item = self.get_achievement(achievement_id)
        name = (payload.get("name") or "").strip()
        if not name:
            raise ValidationError("Название ачивки обязательно.")
        existing = self.achievements.get_by_name(name)
        if existing and existing.id != item.id:
            raise ConflictError("Ачивка с таким названием уже существует.")
        item = self.achievements.update(
            item,
            name=name,
            description=(payload.get("description") or "").strip() or None,
            icon=(payload.get("icon") or "🏆").strip()[:16],
            color=(payload.get("color") or "#4c8bf5").strip()[:30],
            is_active=bool(payload.get("is_active", True)),
        )
        self.audit.log(actor.id, "update_achievement", "achievement", str(item.id), {"name": item.name})
        self.session.commit()
        return item

    def delete_achievement(self, actor: Admin, achievement_id: int):
        item = self.get_achievement(achievement_id)
        self.audit.log(actor.id, "delete_achievement", "achievement", str(item.id), {"name": item.name})
        self.achievements.delete(item)
        self.session.commit()

    def grant_to_admin(self, actor: Admin, admin_id: int, achievement_id: int, note: str | None = None):
        recipient = self.admins.get_by_id(admin_id)
        if not recipient:
            raise NotFoundError("Сотрудник не найден.")
        achievement = self.get_achievement(achievement_id)
        if not achievement.is_active:
            raise ValidationError("Эта ачивка отключена.")
        if self.grants.find_existing(admin_id, achievement_id):
            raise ConflictError("Эта ачивка уже выдана этому сотруднику.")
        grant = self.grants.create(
            admin_id=admin_id,
            achievement_id=achievement_id,
            granted_by_admin_id=actor.id,
            note=(note or "").strip() or None,
        )
        self.notifications.notify_admin(
            admin_id=admin_id,
            kind="achievement_granted",
            title=f"Тебе выдана ачивка: {achievement.name}",
            body=(note or "").strip() or "Открой профиль, чтобы посмотреть награду.",
            link_url=f"/admin/people/{admin_id}",
        )
        self.audit.log(actor.id, "grant_achievement", "admin", str(admin_id), {"achievement_id": achievement_id})
        self.session.commit()
        return grant

    def revoke_grant(self, actor: Admin, grant_id: int):
        grant = self.grants.get_by_id(grant_id)
        if not grant:
            raise NotFoundError("Выдача ачивки не найдена.")
        admin_id = grant.admin_id
        achievement_name = grant.achievement.name if grant.achievement else None
        self.grants.delete(grant)
        self.audit.log(actor.id, "revoke_achievement", "admin", str(admin_id), {"achievement": achievement_name})
        self.session.commit()
