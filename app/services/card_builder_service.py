from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.repositories.access_code_repository import AccessCodeRepository
from app.repositories.media_asset_repository import MediaAssetRepository
from app.repositories.media_episode_repository import MediaEpisodeRepository
from app.repositories.media_season_repository import MediaSeasonRepository
from app.repositories.media_title_repository import MediaTitleRepository
from app.services.audit_service import AuditService
from app.services.code_service import CodeService
from app.services.media_upload_service import MediaUploadService
from app.services.title_metadata_service import pack_title_description


@dataclass
class CardBuildResult:
    title_id: int
    season_id: int | None
    episode_id: int | None
    asset_id: int | None
    code_id: int | None
    code_value: str | None
    asset_storage_kind: str | None
    asset_type: str | None


class CardBuilderService:
    def __init__(self, session: Session):
        self.session = session
        self.audit = AuditService(session)
        self.title_repo = MediaTitleRepository(session)
        self.season_repo = MediaSeasonRepository(session)
        self.episode_repo = MediaEpisodeRepository(session)
        self.asset_repo = MediaAssetRepository(session)
        self.code_repo = AccessCodeRepository(session)
        self.code_service = CodeService(session)
        self.upload_service = MediaUploadService()

    async def create_card(
        self,
        admin_id: int,
        payload: dict,
        upload_file_name: str | None = None,
        upload_file_content_type: str | None = None,
        upload_file_bytes: bytes | None = None,
    ) -> CardBuildResult:
        title_title = (payload.get("title") or "").strip()
        if not title_title:
            raise ValidationError("Название обязательно")

        # Fixed default type for simplified creator
        title_type = "anime"

        uploaded_media = None
        if upload_file_bytes:
            asset_type = (payload.get("asset_type") or "image").strip().lower()
            uploaded_media = await self.upload_service.upload_uploaded_file(
                file_bytes=upload_file_bytes,
                file_name=upload_file_name or "upload.bin",
                content_type=upload_file_content_type,
                asset_type=asset_type,
            )

        title = self.title_repo.create(
            type=title_type,
            title=title_title,
            original_title=(payload.get("original_title") or "").strip() or None,
            description=pack_title_description(
                payload.get("genre"),
                (payload.get("title_description") or "").strip() or None,
            ),
            year=payload.get("year"),
            status="draft",
        )
        self.audit.log(admin_id, "create_media_title", "media_title", str(title.id), {"title": title.title})

        season = None
        if payload.get("season_number") is not None:
            season = self.season_repo.create(
                title_id=title.id,
                season_number=payload["season_number"],
                name=(payload.get("season_name") or "").strip() or None,
                description=None,
            )
            self.audit.log(admin_id, "create_media_season", "media_season", str(season.id), {"title_id": title.id})

        episode = None
        if payload.get("episode_number") is not None:
            episode = self.episode_repo.create(
                title_id=title.id,
                season_id=season.id if season else None,
                episode_number=payload["episode_number"],
                name=(payload.get("episode_name") or "").strip() or None,
                synopsis=(payload.get("episode_synopsis") or "").strip() or None,
                status="draft",
            )
            self.audit.log(admin_id, "create_media_episode", "media_episode", str(episode.id), {"title_id": title.id})

        asset = None
        external_url = (payload.get("external_url") or "").strip()
        if uploaded_media or external_url:
            asset_type = (payload.get("asset_type") or "image").strip().lower()
            storage_kind = "telegram_file_id" if uploaded_media else "external_url"
            telegram_file_id = uploaded_media["telegram_file_id"] if uploaded_media else None
            mime_type = uploaded_media["mime_type"] if uploaded_media else ((payload.get("mime_type") or "").strip() or None)

            if storage_kind == "external_url" and not external_url:
                raise ValidationError("Внешняя ссылка пуста")

            if payload.get("is_primary"):
                self.asset_repo.unset_primary_for_scope(
                    title.id,
                    season.id if season else None,
                    episode.id if episode else None,
                )

            asset = self.asset_repo.create(
                title_id=title.id,
                season_id=season.id if season else None,
                episode_id=episode.id if episode else None,
                asset_type=uploaded_media["asset_type"] if uploaded_media else asset_type,
                storage_kind=storage_kind,
                telegram_file_id=telegram_file_id,
                external_url=None if uploaded_media else external_url,
                mime_type=mime_type,
                is_primary=bool(payload.get("is_primary")),
            )
            self.audit.log(admin_id, "create_media_asset", "media_asset", str(asset.id), {"title_id": title.id})

        code = None
        if payload.get("generate_code", True):
            generated = self.code_service.generate_codes(
                admin_id,
                {
                    "quantity": 1,
                    "title_id": title.id,
                    "season_id": season.id if season else None,
                    "episode_id": episode.id if episode else None,
                    "status": (payload.get("code_status") or "active").strip(),
                },
            )
            code = generated[0]

        self.session.commit()
        self.session.refresh(title)
        if season:
            self.session.refresh(season)
        if episode:
            self.session.refresh(episode)
        if asset:
            self.session.refresh(asset)
        if code:
            self.session.refresh(code)

        return CardBuildResult(
            title_id=title.id,
            season_id=season.id if season else None,
            episode_id=episode.id if episode else None,
            asset_id=asset.id if asset else None,
            code_id=code.id if code else None,
            code_value=code.code if code else None,
            asset_storage_kind=asset.storage_kind if asset else None,
            asset_type=asset.asset_type if asset else None,
        )
