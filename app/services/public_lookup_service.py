from sqlalchemy.orm import Session

from app.models.media_asset import MediaAsset
from app.repositories.access_code_repository import AccessCodeRepository
from app.repositories.media_asset_repository import MediaAssetRepository
from app.schemas.public_lookup import PublicLookupResponse
from app.services.analytics_service import AnalyticsService
from app.services.code_service import CodeService
from app.services.media_service import MediaService


class PublicLookupService:
    def __init__(self, session: Session):
        self.session = session
        self.codes = CodeService(session)
        self.access_codes = AccessCodeRepository(session)
        self.media = MediaService(session)
        self.assets = MediaAssetRepository(session)
        self.analytics = AnalyticsService(session)

    def lookup(self, code: str, source: str = "public_api") -> PublicLookupResponse:
        try:
            access_code = self.codes.lookup_active_code(code)
            response = self._build_response(access_code)
            self.analytics.record_lookup_attempt(
                code_value=code,
                is_found=True,
                source=source,
                access_code=access_code,
                error_text=None,
            )
            return response
        except Exception as exc:
            fallback_code = self.access_codes.get_by_code(code)
            self.analytics.record_lookup_attempt(
                code_value=code,
                is_found=False,
                source=source,
                access_code=fallback_code,
                error_text=str(exc),
            )
            raise

    def _build_response(self, access_code) -> PublicLookupResponse:
        title = self.media.get_title(access_code.title_id) if access_code.title_id else None
        season = self.media.get_season(access_code.season_id) if access_code.season_id else None
        episode = self.media.get_episode(access_code.episode_id) if access_code.episode_id else None

        if episode and not title:
            title = self.media.get_title(episode.title_id)
        if episode and not season and episode.season_id:
            season = self.media.get_season(episode.season_id)
        if season and not title:
            title = self.media.get_title(season.title_id)

        selected_asset = self._pick_best_asset(
            title_id=title.id if title else None,
            season_id=season.id if season else None,
            episode_id=episode.id if episode else None,
        )

        has_media = bool(selected_asset and (selected_asset.telegram_file_id or selected_asset.external_url))

        return PublicLookupResponse(
            code=access_code.code,
            title_id=title.id if title else None,
            title=title.title if title else None,
            original_title=None,
            genre=title.type if title else None,
            title_type=title.type if title else None,
            title_status=title.status if title else None,
            year=None,
            season_id=season.id if season else None,
            season_number=season.season_number if season else None,
            season_name=None,
            episode_id=episode.id if episode else None,
            episode_number=episode.episode_number if episode else None,
            episode_name=None,
            episode_status=episode.status if episode else None,
            description=None,
            asset_id=selected_asset.id if selected_asset else None,
            asset_type=selected_asset.asset_type if selected_asset else None,
            storage_kind=selected_asset.storage_kind if selected_asset else None,
            telegram_file_id=selected_asset.telegram_file_id if selected_asset else None,
            external_url=selected_asset.external_url if selected_asset else None,
            mime_type=selected_asset.mime_type if selected_asset else None,
            has_media=has_media,
        )

    def _pick_best_asset(self, title_id: int | None, season_id: int | None, episode_id: int | None) -> MediaAsset | None:
        candidates = self.assets.list_lookup_candidates(
            title_id=title_id,
            season_id=season_id,
            episode_id=episode_id,
        )
        if not candidates:
            return None

        def scope_priority(asset: MediaAsset) -> int:
            if episode_id and asset.episode_id == episode_id:
                return 0
            if season_id and asset.season_id == season_id:
                return 1
            if title_id and asset.title_id == title_id:
                return 2
            return 3

        def primary_priority(asset: MediaAsset) -> int:
            return 0 if asset.is_primary else 1

        def media_priority(asset: MediaAsset) -> int:
            if asset.asset_type == "video":
                return 0
            if asset.asset_type in {"image", "poster"}:
                return 1
            return 2

        def source_priority(asset: MediaAsset) -> int:
            if asset.storage_kind == "telegram_file_id" and asset.telegram_file_id:
                return 0
            if asset.storage_kind == "external_url" and asset.external_url:
                return 1
            return 2

        ordered = sorted(
            candidates,
            key=lambda item: (
                scope_priority(item),
                primary_priority(item),
                media_priority(item),
                source_priority(item),
                -item.id,
            ),
        )
        return ordered[0]
