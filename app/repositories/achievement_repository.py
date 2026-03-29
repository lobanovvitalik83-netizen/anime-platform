from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.achievement import Achievement
from app.models.admin_achievement import AdminAchievement


class AchievementRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_achievements(self) -> list[Achievement]:
        stmt = select(Achievement).options(joinedload(Achievement.created_by_admin)).order_by(Achievement.created_at.desc())
        return list(self.session.scalars(stmt).unique())

    def list_active_achievements(self) -> list[Achievement]:
        stmt = select(Achievement).where(Achievement.is_active == True).options(joinedload(Achievement.created_by_admin)).order_by(Achievement.title.asc())  # noqa: E712
        return list(self.session.scalars(stmt).unique())

    def get_achievement(self, achievement_id: int) -> Achievement | None:
        stmt = select(Achievement).where(Achievement.id == achievement_id).options(joinedload(Achievement.created_by_admin))
        return self.session.scalar(stmt)

    def get_achievement_by_title(self, title: str) -> Achievement | None:
        stmt = select(Achievement).where(Achievement.title == title)
        return self.session.scalar(stmt)

    def create_achievement(self, **kwargs) -> Achievement:
        entity = Achievement(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update_achievement(self, entity: Achievement, **kwargs) -> Achievement:
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity

    def delete_achievement(self, entity: Achievement) -> None:
        self.session.delete(entity)
        self.session.flush()

    def list_grants_for_admin(self, admin_id: int) -> list[AdminAchievement]:
        stmt = (
            select(AdminAchievement)
            .where(AdminAchievement.admin_id == admin_id)
            .options(joinedload(AdminAchievement.achievement), joinedload(AdminAchievement.granted_by_admin))
            .order_by(AdminAchievement.created_at.desc())
        )
        return list(self.session.scalars(stmt).unique())

    def get_grant(self, grant_id: int) -> AdminAchievement | None:
        stmt = (
            select(AdminAchievement)
            .where(AdminAchievement.id == grant_id)
            .options(joinedload(AdminAchievement.achievement), joinedload(AdminAchievement.granted_by_admin), joinedload(AdminAchievement.admin))
        )
        return self.session.scalar(stmt)

    def grant(self, **kwargs) -> AdminAchievement:
        entity = AdminAchievement(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete_grant(self, entity: AdminAchievement) -> None:
        self.session.delete(entity)
        self.session.flush()
