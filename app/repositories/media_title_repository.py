from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.media_title import MediaTitle


class MediaTitleRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[MediaTitle]:
        statement = select(MediaTitle).order_by(MediaTitle.id.desc())
        return list(self.session.scalars(statement))

    def get_by_id(self, title_id: int) -> MediaTitle | None:
        return self.session.get(MediaTitle, title_id)

    def create(self, **kwargs) -> MediaTitle:
        entity = MediaTitle(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: MediaTitle, **kwargs) -> MediaTitle:
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity
