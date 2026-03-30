from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.achievement import Achievement
from app.models.admin_achievement import AdminAchievement


class AchievementRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[Achievement]:
        stmt = select(Achievement).order_by(Achievement.created_at.desc())
        return list(self.session.scalars(stmt))

    def list_active(self) -> list[Achievement]:
        stmt = select(Achievement).where(Achievement.is_active.is_(True)).order_by(Achievement.name.asc())
        return list(self.session.scalars(stmt))

    def get_by_id(self, achievement_id: int) -> Achievement | None:
        return self.session.get(Achievement, achievement_id)

    def get_by_name(self, name: str) -> Achievement | None:
        stmt = select(Achievement).where(Achievement.name == name)
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


class AdminAchievementRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_for_admin(self, admin_id: int) -> list[AdminAchievement]:
        stmt = (
            select(AdminAchievement)
            .where(AdminAchievement.admin_id == admin_id)
            .options(
                selectinload(AdminAchievement.achievement),
                selectinload(AdminAchievement.granted_by_admin),
            )
            .order_by(AdminAchievement.created_at.desc())
        )
        return list(self.session.scalars(stmt))

    def get_by_id(self, grant_id: int) -> AdminAchievement | None:
        stmt = (
            select(AdminAchievement)
            .where(AdminAchievement.id == grant_id)
            .options(
                selectinload(AdminAchievement.achievement),
                selectinload(AdminAchievement.granted_by_admin),
            )
        )
        return self.session.scalar(stmt)

    def find_existing(self, admin_id: int, achievement_id: int) -> AdminAchievement | None:
        stmt = select(AdminAchievement).where(
            AdminAchievement.admin_id == admin_id,
            AdminAchievement.achievement_id == achievement_id,
        )
        return self.session.scalar(stmt)

    def create(self, **kwargs) -> AdminAchievement:
        entity = AdminAchievement(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: AdminAchievement) -> None:
        self.session.delete(entity)
        self.session.flush()
