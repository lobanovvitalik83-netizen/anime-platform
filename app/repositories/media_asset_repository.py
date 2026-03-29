from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.media_asset import MediaAsset


class MediaAssetRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(
        self,
        title_id: int | None = None,
        season_id: int | None = None,
        episode_id: int | None = None,
    ) -> list[MediaAsset]:
        statement = select(MediaAsset)
        if title_id is not None:
            statement = statement.where(MediaAsset.title_id == title_id)
        if season_id is not None:
            statement = statement.where(MediaAsset.season_id == season_id)
        if episode_id is not None:
            statement = statement.where(MediaAsset.episode_id == episode_id)
        statement = statement.order_by(MediaAsset.id.desc())
        return list(self.session.scalars(statement))

    def get_by_id(self, asset_id: int) -> MediaAsset | None:
        return self.session.get(MediaAsset, asset_id)

    def create(self, **kwargs) -> MediaAsset:
        entity = MediaAsset(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: MediaAsset, **kwargs) -> MediaAsset:
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity

    def unset_primary_for_scope(self, title_id: int | None, season_id: int | None, episode_id: int | None) -> None:
        statement = select(MediaAsset).where(
            MediaAsset.title_id.is_(title_id) if title_id is None else MediaAsset.title_id == title_id,
            MediaAsset.season_id.is_(season_id) if season_id is None else MediaAsset.season_id == season_id,
            MediaAsset.episode_id.is_(episode_id) if episode_id is None else MediaAsset.episode_id == episode_id,
            MediaAsset.is_primary.is_(True),
        )
        for entity in self.session.scalars(statement):
            entity.is_primary = False
        self.session.flush()

    def list_lookup_candidates(self, title_id: int | None, season_id: int | None, episode_id: int | None) -> list[MediaAsset]:
        conditions = []
        if episode_id is not None:
            conditions.append(MediaAsset.episode_id == episode_id)
        if season_id is not None:
            conditions.append(MediaAsset.season_id == season_id)
        if title_id is not None:
            conditions.append(MediaAsset.title_id == title_id)
        if not conditions:
            return []
        statement = select(MediaAsset).where(or_(*conditions)).order_by(MediaAsset.id.desc())
        return list(self.session.scalars(statement))
