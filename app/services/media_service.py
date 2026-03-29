from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.media_episode import MediaEpisode
from app.models.media_season import MediaSeason
from app.models.media_title import MediaTitle
from app.repositories.media_episode_repository import MediaEpisodeRepository
from app.repositories.media_season_repository import MediaSeasonRepository
from app.repositories.media_title_repository import MediaTitleRepository
from app.services.audit_service import AuditService


class MediaService:
    def __init__(self, session: Session):
        self.session = session
        self.titles = MediaTitleRepository(session)
        self.seasons = MediaSeasonRepository(session)
        self.episodes = MediaEpisodeRepository(session)
        self.audit = AuditService(session)

    def list_titles(self) -> list[MediaTitle]:
        return self.titles.list_all()

    def get_title(self, title_id: int) -> MediaTitle:
        entity = self.titles.get_by_id(title_id)
        if not entity:
            raise NotFoundError("Media title not found")
        return entity

    def create_title(self, admin_id: int, payload: dict) -> MediaTitle:
        entity = self.titles.create(**payload)
        self.audit.log(admin_id, "create_media_title", "media_title", str(entity.id), {"title": entity.title})
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update_title(self, admin_id: int, title_id: int, payload: dict) -> MediaTitle:
        entity = self.get_title(title_id)
        entity = self.titles.update(entity, **payload)
        self.audit.log(admin_id, "update_media_title", "media_title", str(entity.id), payload)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete_title(self, admin_id: int, title_id: int) -> None:
        entity = self.get_title(title_id)
        self.audit.log(admin_id, "delete_media_title", "media_title", str(entity.id), {"title": entity.title})
        self.titles.delete(entity)
        self.session.commit()

    def list_seasons(self, title_id: int | None = None) -> list[MediaSeason]:
        return self.seasons.list_all(title_id=title_id)

    def get_season(self, season_id: int) -> MediaSeason:
        entity = self.seasons.get_by_id(season_id)
        if not entity:
            raise NotFoundError("Media season not found")
        return entity

    def create_season(self, admin_id: int, payload: dict) -> MediaSeason:
        self.get_title(payload["title_id"])
        entity = self.seasons.create(**payload)
        self.audit.log(admin_id, "create_media_season", "media_season", str(entity.id), payload)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update_season(self, admin_id: int, season_id: int, payload: dict) -> MediaSeason:
        entity = self.get_season(season_id)
        if payload.get("title_id") is not None:
            self.get_title(payload["title_id"])
        entity = self.seasons.update(entity, **payload)
        self.audit.log(admin_id, "update_media_season", "media_season", str(entity.id), payload)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete_season(self, admin_id: int, season_id: int) -> None:
        entity = self.get_season(season_id)
        self.audit.log(admin_id, "delete_media_season", "media_season", str(entity.id), {"season_number": entity.season_number})
        self.seasons.delete(entity)
        self.session.commit()

    def list_episodes(self, title_id: int | None = None, season_id: int | None = None) -> list[MediaEpisode]:
        return self.episodes.list_all(title_id=title_id, season_id=season_id)

    def get_episode(self, episode_id: int) -> MediaEpisode:
        entity = self.episodes.get_by_id(episode_id)
        if not entity:
            raise NotFoundError("Media episode not found")
        return entity

    def create_episode(self, admin_id: int, payload: dict) -> MediaEpisode:
        self.get_title(payload["title_id"])
        season_id = payload.get("season_id")
        if season_id is not None:
            season = self.get_season(season_id)
            if season.title_id != payload["title_id"]:
                raise NotFoundError("Season does not belong to title")

        entity = self.episodes.create(**payload)
        self.audit.log(admin_id, "create_media_episode", "media_episode", str(entity.id), payload)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update_episode(self, admin_id: int, episode_id: int, payload: dict) -> MediaEpisode:
        entity = self.get_episode(episode_id)

        target_title_id = payload.get("title_id", entity.title_id)
        self.get_title(target_title_id)

        if payload.get("season_id") is not None:
            season = self.get_season(payload["season_id"])
            if season.title_id != target_title_id:
                raise NotFoundError("Season does not belong to episode title")

        entity = self.episodes.update(entity, **payload)
        self.audit.log(admin_id, "update_media_episode", "media_episode", str(entity.id), payload)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete_episode(self, admin_id: int, episode_id: int) -> None:
        entity = self.get_episode(episode_id)
        self.audit.log(admin_id, "delete_media_episode", "media_episode", str(entity.id), {"episode_number": entity.episode_number})
        self.episodes.delete(entity)
        self.session.commit()
