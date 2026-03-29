from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.achievement import Achievement
from app.models.admin_achievement import AdminAchievement


class AchievementRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[Achievement]:
        stmt = select(Achievement).order_by(Achievement.title.asc())
        return list(self.session.scalars(stmt))

    def list_active(self) -> list[Achievement]:
        stmt = select(Achievement).where(Achievement.is_active.is_(True)).order_by(Achievement.title.asc())
        return list(self.session.scalars(stmt))

    def get_by_id(self, achievement_id: int) -> Achievement | None:
        return self.session.get(Achievement, achievement_id)

    def get_by_slug(self, slug: str) -> Achievement | None:
        stmt = select(Achievement).where(Achievement.slug == slug)
        return self.session.scalar(stmt)

    def create(self, **kwargs) -> Achievement:
        entity = Achievement(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: Achievement, **kwargs) -> Achievement:
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity

    def delete(self, entity: Achievement) -> None:
        self.session.delete(entity)
        self.session.flush()

    def list_admin_grants(self, admin_id: int) -> list[AdminAchievement]:
        stmt = (
            select(AdminAchievement)
            .where(AdminAchievement.admin_id == admin_id)
            .options(joinedload(AdminAchievement.achievement), joinedload(AdminAchievement.issued_by_admin))
            .order_by(AdminAchievement.created_at.desc())
        )
        return list(self.session.scalars(stmt).unique())

    def has_grant(self, admin_id: int, achievement_id: int) -> AdminAchievement | None:
        stmt = select(AdminAchievement).where(
            AdminAchievement.admin_id == admin_id,
            AdminAchievement.achievement_id == achievement_id,
        )
        return self.session.scalar(stmt)

    def grant(self, **kwargs) -> AdminAchievement:
        entity = AdminAchievement(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def revoke(self, entity: AdminAchievement) -> None:
        self.session.delete(entity)
        self.session.flush()
