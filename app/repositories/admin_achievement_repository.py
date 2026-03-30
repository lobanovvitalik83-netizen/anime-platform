from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.admin_achievement import AdminAchievement


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
            .order_by(AdminAchievement.display_order.asc(), AdminAchievement.created_at.desc())
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

    def update(self, entity: AdminAchievement, **kwargs) -> AdminAchievement:
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity

    def delete(self, entity: AdminAchievement) -> None:
        self.session.delete(entity)
        self.session.flush()
