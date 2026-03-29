from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin_achievement import AdminAchievement


class AdminAchievementRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_for_admin(self, admin_id: int) -> list[AdminAchievement]:
        statement = select(AdminAchievement).where(AdminAchievement.admin_id == admin_id).order_by(AdminAchievement.created_at.desc())
        return list(self.session.scalars(statement))

    def get_by_id(self, grant_id: int) -> AdminAchievement | None:
        return self.session.get(AdminAchievement, grant_id)

    def get_for_admin_and_achievement(self, admin_id: int, achievement_id: int) -> AdminAchievement | None:
        statement = select(AdminAchievement).where(
            AdminAchievement.admin_id == admin_id,
            AdminAchievement.achievement_id == achievement_id,
        )
        return self.session.scalar(statement)

    def create(self, **kwargs) -> AdminAchievement:
        entity = AdminAchievement(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: AdminAchievement) -> None:
        self.session.delete(entity)
        self.session.flush()
