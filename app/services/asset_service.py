from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
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
        return self.assets.list_assets(title_id=title_id, season_id=season_id, episode_id=episode_id)

    def get_asset(self, asset_id: int) -> MediaAsset:
        entity = self.assets.get_by_id(asset_id)
        if not entity:
            raise NotFoundError("Media asset not found")
        return entity

    def create_asset(self, admin_id: int, payload: dict) -> MediaAsset:
        payload = self._normalize_payload(payload)

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
        payload = self._normalize_payload(payload, partial=True)

        if payload.get("is_primary") is True:
            self.assets.unset_primary_for_scope(entity.title_id, entity.season_id, entity.episode_id)

        entity = self.assets.update(entity, **payload)
        self.audit.log(admin_id, "update_media_asset", "media_asset", str(entity.id), payload)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def _normalize_payload(self, payload: dict, partial: bool = False) -> dict:
        normalized = dict(payload)
        storage_kind = normalized.get("storage_kind")

        if storage_kind == "external_url":
            external_url = (normalized.get("external_url") or "").strip()
            if not external_url:
                raise ValidationError("external_url is required for storage_kind=external_url")
            normalized["external_url"] = external_url
            normalized["telegram_file_id"] = None

        elif storage_kind == "telegram_file_id":
            telegram_file_id = (normalized.get("telegram_file_id") or "").strip()
            if not telegram_file_id:
                raise ValidationError("telegram_file_id is required for storage_kind=telegram_file_id")
            normalized["telegram_file_id"] = telegram_file_id
            normalized["external_url"] = None

        elif not partial:
            raise ValidationError("storage_kind must be external_url or telegram_file_id")

        owner_count = sum(
            1
            for key in ("title_id", "season_id", "episode_id")
            if normalized.get(key) is not None
        )
        if not partial and owner_count == 0:
            raise ValidationError("At least one owner must be provided")

        return normalized
