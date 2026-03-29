from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.achievement import Achievement


class AchievementRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[Achievement]:
        return list(self.session.scalars(select(Achievement).order_by(Achievement.title.asc())))

    def get_by_id(self, achievement_id: int) -> Achievement | None:
        return self.session.get(Achievement, achievement_id)

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
