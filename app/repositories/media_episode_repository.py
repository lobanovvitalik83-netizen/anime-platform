from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.media_episode import MediaEpisode


class MediaEpisodeRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self, title_id: int | None = None, season_id: int | None = None) -> list[MediaEpisode]:
        statement = select(MediaEpisode)
        if title_id is not None:
            statement = statement.where(MediaEpisode.title_id == title_id)
        if season_id is not None:
            statement = statement.where(MediaEpisode.season_id == season_id)
        statement = statement.order_by(MediaEpisode.id.desc())
        return list(self.session.scalars(statement))

    def get_by_id(self, episode_id: int) -> MediaEpisode | None:
        return self.session.get(MediaEpisode, episode_id)

    def create(self, **kwargs) -> MediaEpisode:
        entity = MediaEpisode(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: MediaEpisode, **kwargs) -> MediaEpisode:
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity

    def delete(self, entity: MediaEpisode) -> None:
        self.session.delete(entity)
        self.session.flush()
