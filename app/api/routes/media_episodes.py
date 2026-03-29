from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db_session
from app.models.admin import Admin
from app.schemas.media_episode import MediaEpisodeCreate, MediaEpisodeRead, MediaEpisodeUpdate
from app.services.media_service import MediaService

router = APIRouter(prefix="/api/media-episodes", tags=["media-episodes"])


@router.get("", response_model=list[MediaEpisodeRead])
def list_media_episodes(
    title_id: int | None = Query(default=None),
    season_id: int | None = Query(default=None),
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> list[MediaEpisodeRead]:
    items = MediaService(db).list_episodes(title_id=title_id, season_id=season_id)
    return [MediaEpisodeRead.model_validate(item) for item in items]


@router.post("", response_model=MediaEpisodeRead)
def create_media_episode(
    payload: MediaEpisodeCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> MediaEpisodeRead:
    item = MediaService(db).create_episode(current_admin.id, payload.model_dump())
    return MediaEpisodeRead.model_validate(item)


@router.get("/{episode_id}", response_model=MediaEpisodeRead)
def get_media_episode(
    episode_id: int,
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> MediaEpisodeRead:
    item = MediaService(db).get_episode(episode_id)
    return MediaEpisodeRead.model_validate(item)


@router.patch("/{episode_id}", response_model=MediaEpisodeRead)
def update_media_episode(
    episode_id: int,
    payload: MediaEpisodeUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> MediaEpisodeRead:
    item = MediaService(db).update_episode(current_admin.id, episode_id, payload.model_dump(exclude_unset=True))
    return MediaEpisodeRead.model_validate(item)
