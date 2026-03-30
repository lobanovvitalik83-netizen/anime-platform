from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.achievement import Achievement
from app.models.admin_achievement import AdminAchievement
from app.services.audit_service import AuditService


class AchievementService:
    def __init__(self, session: Session):
        self.session = session
        self.audit = AuditService(session)

    def list_achievements(self) -> list[Achievement]:
        return list(self.session.scalars(select(Achievement).order_by(Achievement.name.asc())))

    def get_achievement(self, achievement_id: int) -> Achievement:
        entity = self.session.get(Achievement, achievement_id)
        if not entity:
            raise NotFoundError("Ачивка не найдена.")
        return entity

    def create_achievement(self, actor_id: int, *, name: str, description: str | None, icon_url: str | None, is_active: bool) -> Achievement:
        name = (name or "").strip()
        if len(name) < 2:
            raise ValidationError("Название ачивки слишком короткое.")
        existing = self.session.scalar(select(Achievement).where(Achievement.name == name))
        if existing:
            raise ConflictError("Ачивка с таким названием уже существует.")
        entity = Achievement(name=name, description=(description or "").strip() or None, icon_url=(icon_url or "").strip() or None, is_active=is_active)
        self.session.add(entity)
        self.session.flush()
        self.audit.log(actor_id, "create_achievement", "achievement", str(entity.id), {"name": entity.name})
        self.session.commit()
        return entity

    def update_achievement(self, actor_id: int, achievement_id: int, *, name: str, description: str | None, icon_url: str | None, is_active: bool) -> Achievement:
        entity = self.get_achievement(achievement_id)
        name = (name or "").strip()
        if len(name) < 2:
            raise ValidationError("Название ачивки слишком короткое.")
        existing = self.session.scalar(select(Achievement).where(Achievement.name == name, Achievement.id != entity.id))
        if existing:
            raise ConflictError("Ачивка с таким названием уже существует.")
        entity.name = name
        entity.description = (description or "").strip() or None
        entity.icon_url = (icon_url or "").strip() or None
        entity.is_active = is_active
        self.session.flush()
        self.audit.log(actor_id, "update_achievement", "achievement", str(entity.id), {"name": entity.name})
        self.session.commit()
        return entity

    def delete_achievement(self, actor_id: int, achievement_id: int) -> None:
        entity = self.get_achievement(achievement_id)
        self.audit.log(actor_id, "delete_achievement", "achievement", str(entity.id), {"name": entity.name})
        self.session.delete(entity)
        self.session.commit()

    def list_admin_grants(self, admin_id: int) -> list[AdminAchievement]:
        stmt = (
            select(AdminAchievement)
            .where(AdminAchievement.admin_id == admin_id)
            .options(selectinload(AdminAchievement.achievement), selectinload(AdminAchievement.granted_by_admin))
            .order_by(AdminAchievement.created_at.desc())
        )
        return list(self.session.scalars(stmt))

    def grant(self, actor_id: int, *, admin_id: int, achievement_id: int, reason: str | None) -> AdminAchievement:
        existing = self.session.scalar(
            select(AdminAchievement).where(
                AdminAchievement.admin_id == admin_id,
                AdminAchievement.achievement_id == achievement_id,
            )
        )
        if existing:
            raise ConflictError("Эта ачивка уже выдана сотруднику.")
        entity = AdminAchievement(
            admin_id=admin_id,
            achievement_id=achievement_id,
            reason=(reason or "").strip() or None,
            granted_by_admin_id=actor_id,
            source="manual",
        )
        self.session.add(entity)
        self.session.flush()
        self.audit.log(actor_id, "grant_achievement", "admin", str(admin_id), {"achievement_id": achievement_id})
        self.session.commit()
        return entity

    def revoke(self, actor_id: int, grant_id: int) -> None:
        entity = self.session.get(AdminAchievement, grant_id)
        if not entity:
            raise NotFoundError("Выдача ачивки не найдена.")
        self.audit.log(actor_id, "revoke_achievement", "admin", str(entity.admin_id), {"achievement_id": entity.achievement_id})
        self.session.delete(entity)
        self.session.commit()
