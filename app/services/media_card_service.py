from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.repositories.access_code_repository import AccessCodeRepository
from app.repositories.media_asset_repository import MediaAssetRepository
from app.repositories.media_episode_repository import MediaEpisodeRepository
from app.repositories.media_season_repository import MediaSeasonRepository
from app.repositories.media_title_repository import MediaTitleRepository
from app.services.audit_service import AuditService
from app.services.code_service import CodeService
from app.services.media_upload_service import MediaUploadService
from app.services.media_service import MediaService


@dataclass
class MediaCardRow:
    title_id: int
    genre: str
    title: str
    status: str
    season_id: int | None
    season_number: int | None
    episode_id: int | None
    episode_number: int | None
    asset_id: int | None
    asset_type: str | None
    storage_kind: str | None
    telegram_file_id: str | None
    external_url: str | None
    code_id: int | None
    code_value: str | None
    created_at: Any


class MediaCardService:
    def __init__(self, session: Session):
        self.session = session
        self.audit = AuditService(session)
        self.media_service = MediaService(session)
        self.title_repo = MediaTitleRepository(session)
        self.season_repo = MediaSeasonRepository(session)
        self.episode_repo = MediaEpisodeRepository(session)
        self.asset_repo = MediaAssetRepository(session)
        self.code_repo = AccessCodeRepository(session)
        self.code_service = CodeService(session)
        self.upload_service = MediaUploadService()

    def list_cards(self) -> list[MediaCardRow]:
        rows: list[MediaCardRow] = []
        titles = self.media_service.list_titles()
        for title in titles:
            seasons = self.media_service.list_seasons(title_id=title.id)
            episodes = self.media_service.list_episodes(title_id=title.id)
            assets = self.asset_repo.list_all(title_id=title.id)
            codes = [item for item in self.code_service.list_codes() if item.title_id == title.id]

            season = seasons[0] if seasons else None
            episode = episodes[0] if episodes else None
            asset = self._pick_asset(assets, episode.id if episode else None, season.id if season else None)
            code = codes[0] if codes else None

            rows.append(
                MediaCardRow(
                    title_id=title.id,
                    genre=title.type,
                    title=title.title,
                    status=title.status,
                    season_id=season.id if season else None,
                    season_number=season.season_number if season else None,
                    episode_id=episode.id if episode else None,
                    episode_number=episode.episode_number if episode else None,
                    asset_id=asset.id if asset else None,
                    asset_type=asset.asset_type if asset else None,
                    storage_kind=asset.storage_kind if asset else None,
                    telegram_file_id=asset.telegram_file_id if asset else None,
                    external_url=asset.external_url if asset else None,
                    code_id=code.id if code else None,
                    code_value=code.code if code else None,
                    created_at=title.created_at,
                )
            )
        return rows

    def get_card(self, title_id: int) -> dict:
        title = self.media_service.get_title(title_id)
        seasons = self.media_service.list_seasons(title_id=title.id)
        episodes = self.media_service.list_episodes(title_id=title.id)
        assets = self.asset_repo.list_all(title_id=title.id)
        codes = [item for item in self.code_service.list_codes() if item.title_id == title.id]

        season = seasons[0] if seasons else None
        episode = episodes[0] if episodes else None
        asset = self._pick_asset(assets, episode.id if episode else None, season.id if season else None)
        code = codes[0] if codes else None

        return {
            "title": title,
            "season": season,
            "episode": episode,
            "asset": asset,
            "code": code,
        }

    async def create_card(
        self,
        admin_id: int,
        payload: dict,
        upload_file_name: str | None = None,
        upload_file_content_type: str | None = None,
        upload_file_bytes: bytes | None = None,
    ) -> dict:
        title_name = (payload.get("title") or "").strip()
        if not title_name:
            raise ValidationError("Название обязательно")

        genre = (payload.get("genre") or "").strip().lower()
        if genre not in {"anime", "series", "movie"}:
            raise ValidationError("Жанр должен быть: anime, series или movie")

        status = (payload.get("status") or "draft").strip()

        uploaded_media = None
        if upload_file_bytes:
            uploaded_media = await self.upload_service.upload_uploaded_file(
                file_bytes=upload_file_bytes,
                file_name=upload_file_name or "upload.bin",
                content_type=upload_file_content_type,
                asset_type=(payload.get("asset_type") or "image").strip().lower(),
            )

        title = self.title_repo.create(
            type=genre,
            title=title_name,
            original_title=None,
            description=None,
            year=None,
            status=status,
        )
        self.audit.log(admin_id, "create_media_title", "media_title", str(title.id), {"title": title.title})

        season = None
        if payload.get("season_number") is not None:
            season = self.season_repo.create(
                title_id=title.id,
                season_number=payload["season_number"],
                name=None,
                description=None,
            )
            self.audit.log(admin_id, "create_media_season", "media_season", str(season.id), {"title_id": title.id})

        episode = None
        if payload.get("episode_number") is not None:
            episode = self.episode_repo.create(
                title_id=title.id,
                season_id=season.id if season else None,
                episode_number=payload["episode_number"],
                name=None,
                synopsis=None,
                status=status,
            )
            self.audit.log(admin_id, "create_media_episode", "media_episode", str(episode.id), {"title_id": title.id})

        asset = None
        external_url = (payload.get("external_url") or "").strip()
        if uploaded_media or external_url:
            if payload.get("is_primary"):
                self.asset_repo.unset_primary_for_scope(title.id, season.id if season else None, episode.id if episode else None)

            asset = self.asset_repo.create(
                title_id=title.id,
                season_id=season.id if season else None,
                episode_id=episode.id if episode else None,
                asset_type=uploaded_media["asset_type"] if uploaded_media else (payload.get("asset_type") or "image").strip().lower(),
                storage_kind="telegram_file_id" if uploaded_media else "external_url",
                telegram_file_id=uploaded_media["telegram_file_id"] if uploaded_media else None,
                external_url=None if uploaded_media else external_url,
                mime_type=uploaded_media["mime_type"] if uploaded_media else ((payload.get("mime_type") or "").strip() or None),
                is_primary=bool(payload.get("is_primary")),
            )
            self.audit.log(admin_id, "create_media_asset", "media_asset", str(asset.id), {"title_id": title.id})

        code = None
        if payload.get("generate_code", True):
            code = self.code_service.generate_codes(
                admin_id,
                {
                    "quantity": 1,
                    "title_id": title.id,
                    "season_id": season.id if season else None,
                    "episode_id": episode.id if episode else None,
                    "status": status if status in {"active", "inactive", "archived"} else "active",
                },
            )[0]

        self.session.commit()
        return {
            "title": title,
            "season": season,
            "episode": episode,
            "asset": asset,
            "code": code,
        }

    async def update_card(
        self,
        admin_id: int,
        title_id: int,
        payload: dict,
        upload_file_name: str | None = None,
        upload_file_content_type: str | None = None,
        upload_file_bytes: bytes | None = None,
    ) -> dict:
        card = self.get_card(title_id)
        title = card["title"]
        season = card["season"]
        episode = card["episode"]
        asset = card["asset"]
        code = card["code"]

        title_name = (payload.get("title") or "").strip()
        if not title_name:
            raise ValidationError("Название обязательно")

        genre = (payload.get("genre") or "").strip().lower()
        if genre not in {"anime", "series", "movie"}:
            raise ValidationError("Жанр должен быть: anime, series или movie")

        status = (payload.get("status") or title.status or "draft").strip()

        uploaded_media = None
        if upload_file_bytes:
            uploaded_media = await self.upload_service.upload_uploaded_file(
                file_bytes=upload_file_bytes,
                file_name=upload_file_name or "upload.bin",
                content_type=upload_file_content_type,
                asset_type=(payload.get("asset_type") or "image").strip().lower(),
            )

        title = self.title_repo.update(
            title,
            type=genre,
            title=title_name,
            status=status,
            original_title=None,
            description=None,
            year=None,
        )
        self.audit.log(admin_id, "update_media_title", "media_title", str(title.id), {"title": title.title, "type": genre})

        target_season_number = payload.get("season_number")
        if target_season_number is not None:
            if season:
                season = self.season_repo.update(season, season_number=target_season_number, name=None, description=None, title_id=title.id)
            else:
                season = self.season_repo.create(title_id=title.id, season_number=target_season_number, name=None, description=None)
            self.audit.log(admin_id, "update_media_season", "media_season", str(season.id), {"season_number": target_season_number})

        target_episode_number = payload.get("episode_number")
        if target_episode_number is not None:
            if episode:
                episode = self.episode_repo.update(
                    episode,
                    title_id=title.id,
                    season_id=season.id if season else None,
                    episode_number=target_episode_number,
                    name=None,
                    synopsis=None,
                    status=status,
                )
            else:
                episode = self.episode_repo.create(
                    title_id=title.id,
                    season_id=season.id if season else None,
                    episode_number=target_episode_number,
                    name=None,
                    synopsis=None,
                    status=status,
                )
            self.audit.log(admin_id, "update_media_episode", "media_episode", str(episode.id), {"episode_number": target_episode_number})

        external_url = (payload.get("external_url") or "").strip()
        should_update_asset = bool(uploaded_media or external_url or asset)
        if should_update_asset:
            asset_payload = {
                "title_id": title.id,
                "season_id": season.id if season else None,
                "episode_id": episode.id if episode else None,
                "asset_type": uploaded_media["asset_type"] if uploaded_media else (payload.get("asset_type") or (asset.asset_type if asset else "image")).strip().lower(),
                "storage_kind": "telegram_file_id" if uploaded_media else ("external_url" if external_url else (asset.storage_kind if asset else None)),
                "telegram_file_id": uploaded_media["telegram_file_id"] if uploaded_media else (asset.telegram_file_id if asset else None),
                "external_url": None if uploaded_media else (external_url or (asset.external_url if asset else None)),
                "mime_type": uploaded_media["mime_type"] if uploaded_media else ((payload.get("mime_type") or "").strip() or (asset.mime_type if asset else None)),
                "is_primary": bool(payload.get("is_primary")),
            }

            if asset_payload["storage_kind"] is None:
                raise ValidationError("Нужен файл или внешняя ссылка")

            if payload.get("is_primary"):
                self.asset_repo.unset_primary_for_scope(title.id, season.id if season else None, episode.id if episode else None)

            if asset:
                asset = self.asset_repo.update(asset, **asset_payload)
            else:
                asset = self.asset_repo.create(**asset_payload)
            self.audit.log(admin_id, "update_media_asset", "media_asset", str(asset.id), {"asset_type": asset.asset_type})

        if code:
            self.code_service.update_code(
                admin_id,
                code.id,
                {
                    "code": code.code,
                    "title_id": title.id,
                    "season_id": season.id if season else None,
                    "episode_id": episode.id if episode else None,
                    "status": status if status in {"active", "inactive", "archived"} else code.status,
                },
            )
        elif payload.get("generate_code", True):
            code = self.code_service.generate_codes(
                admin_id,
                {
                    "quantity": 1,
                    "title_id": title.id,
                    "season_id": season.id if season else None,
                    "episode_id": episode.id if episode else None,
                    "status": status if status in {"active", "inactive", "archived"} else "active",
                },
            )[0]

        self.session.commit()
        return {
            "title": title,
            "season": season,
            "episode": episode,
            "asset": asset,
            "code": code,
        }

    def delete_card(self, admin_id: int, title_id: int) -> None:
        title = self.media_service.get_title(title_id)
        seasons = self.media_service.list_seasons(title_id=title_id)
        episodes = self.media_service.list_episodes(title_id=title_id)
        assets = self.asset_repo.list_all(title_id=title_id)
        codes = [item for item in self.code_service.list_codes() if item.title_id == title_id]

        for code in codes:
            self.audit.log(admin_id, "delete_access_code", "access_code", str(code.id), {"code": code.code})
            self.code_repo.delete(code)

        for asset in assets:
            self.audit.log(admin_id, "delete_media_asset", "media_asset", str(asset.id), {"asset_type": asset.asset_type})
            self.asset_repo.delete(asset)

        for episode in episodes:
            self.audit.log(admin_id, "delete_media_episode", "media_episode", str(episode.id), {"episode_number": episode.episode_number})
            self.episode_repo.delete(episode)

        for season in seasons:
            self.audit.log(admin_id, "delete_media_season", "media_season", str(season.id), {"season_number": season.season_number})
            self.season_repo.delete(season)

        self.audit.log(admin_id, "delete_media_title", "media_title", str(title.id), {"title": title.title})
        self.title_repo.delete(title)
        self.session.commit()

    def _pick_asset(self, assets: list, episode_id: int | None, season_id: int | None):
        if not assets:
            return None

        def key(item):
            return (
                0 if episode_id and item.episode_id == episode_id else 1,
                0 if season_id and item.season_id == season_id else 1,
                0 if item.is_primary else 1,
                -item.id,
            )
        assets = sorted(assets, key=key)
        return assets[0]
