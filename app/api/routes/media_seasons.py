from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db_session
from app.models.admin import Admin
from app.schemas.media_season import MediaSeasonCreate, MediaSeasonRead, MediaSeasonUpdate
from app.services.media_service import MediaService

router = APIRouter(prefix="/api/media-seasons", tags=["media-seasons"])


@router.get("", response_model=list[MediaSeasonRead])
def list_media_seasons(
    title_id: int | None = Query(default=None),
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> list[MediaSeasonRead]:
    items = MediaService(db).list_seasons(title_id=title_id)
    return [MediaSeasonRead.model_validate(item) for item in items]


@router.post("", response_model=MediaSeasonRead)
def create_media_season(
    payload: MediaSeasonCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> MediaSeasonRead:
    item = MediaService(db).create_season(current_admin.id, payload.model_dump())
    return MediaSeasonRead.model_validate(item)


@router.get("/{season_id}", response_model=MediaSeasonRead)
def get_media_season(
    season_id: int,
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> MediaSeasonRead:
    item = MediaService(db).get_season(season_id)
    return MediaSeasonRead.model_validate(item)


@router.patch("/{season_id}", response_model=MediaSeasonRead)
def update_media_season(
    season_id: int,
    payload: MediaSeasonUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> MediaSeasonRead:
    item = MediaService(db).update_season(current_admin.id, season_id, payload.model_dump(exclude_unset=True))
    return MediaSeasonRead.model_validate(item)
