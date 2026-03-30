from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.achievement import Achievement


class AchievementRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self, *, active_only: bool = False) -> list[Achievement]:
        stmt = select(Achievement).order_by(Achievement.title.asc())
        if active_only:
            stmt = stmt.where(Achievement.is_active.is_(True))
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
