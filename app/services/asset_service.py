from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.media_asset import MediaAsset
from app.repositories.media_asset_repository import MediaAssetRepository
from app.services.audit_service import AuditService
from app.services.media_service import MediaService


class AssetService:
    def __init__(self, session: Session):
        self.session = session
        self.assets = MediaAssetRepository(session)
        self.media = MediaService(session)
        self.audit = AuditService(session)

    def list_assets(
        self,
        title_id: int | None = None,
        season_id: int | None = None,
        episode_id: int | None = None,
    ) -> list[MediaAsset]:
        return self.assets.list_all(title_id=title_id, season_id=season_id, episode_id=episode_id)

    def get_asset(self, asset_id: int) -> MediaAsset:
        entity = self.assets.get_by_id(asset_id)
        if not entity:
            raise NotFoundError("Media asset not found")
        return entity

    def create_asset(self, admin_id: int, payload: dict) -> MediaAsset:
        if payload.get("title_id") is not None:
            self.media.get_title(payload["title_id"])
        if payload.get("season_id") is not None:
            self.media.get_season(payload["season_id"])
        if payload.get("episode_id") is not None:
            self.media.get_episode(payload["episode_id"])

        if payload.get("is_primary"):
            self.assets.unset_primary_for_scope(
                payload.get("title_id"),
                payload.get("season_id"),
                payload.get("episode_id"),
            )

        entity = self.assets.create(**payload)
        self.audit.log(admin_id, "create_media_asset", "media_asset", str(entity.id), payload)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update_asset(self, admin_id: int, asset_id: int, payload: dict) -> MediaAsset:
        entity = self.get_asset(asset_id)

        if payload.get("is_primary") is True:
            self.assets.unset_primary_for_scope(entity.title_id, entity.season_id, entity.episode_id)

        entity = self.assets.update(entity, **payload)
        self.audit.log(admin_id, "update_media_asset", "media_asset", str(entity.id), payload)
        self.session.commit()
        self.session.refresh(entity)
        return entity
