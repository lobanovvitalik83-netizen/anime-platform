from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.media_season import MediaSeason


class MediaSeasonRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self, title_id: int | None = None) -> list[MediaSeason]:
        statement = select(MediaSeason)
        if title_id is not None:
            statement = statement.where(MediaSeason.title_id == title_id)
        statement = statement.order_by(MediaSeason.id.desc())
        return list(self.session.scalars(statement))

    def get_by_id(self, season_id: int) -> MediaSeason | None:
        return self.session.get(MediaSeason, season_id)

    def create(self, **kwargs) -> MediaSeason:
        entity = MediaSeason(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: MediaSeason, **kwargs) -> MediaSeason:
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity

    def delete(self, entity: MediaSeason) -> None:
        self.session.delete(entity)
        self.session.flush()
