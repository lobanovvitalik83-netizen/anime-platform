from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db_session
from app.models.admin import Admin
from app.schemas.media_asset import MediaAssetCreate, MediaAssetRead, MediaAssetUpdate
from app.services.asset_service import AssetService

router = APIRouter(prefix="/api/media-assets", tags=["media-assets"])


@router.get("", response_model=list[MediaAssetRead])
def list_media_assets(
    title_id: int | None = Query(default=None),
    season_id: int | None = Query(default=None),
    episode_id: int | None = Query(default=None),
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> list[MediaAssetRead]:
    items = AssetService(db).list_assets(title_id=title_id, season_id=season_id, episode_id=episode_id)
    return [MediaAssetRead.model_validate(item) for item in items]


@router.post("", response_model=MediaAssetRead)
def create_media_asset(
    payload: MediaAssetCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> MediaAssetRead:
    item = AssetService(db).create_asset(current_admin.id, payload.model_dump())
    return MediaAssetRead.model_validate(item)


@router.get("/{asset_id}", response_model=MediaAssetRead)
def get_media_asset(
    asset_id: int,
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> MediaAssetRead:
    item = AssetService(db).get_asset(asset_id)
    return MediaAssetRead.model_validate(item)


@router.patch("/{asset_id}", response_model=MediaAssetRead)
def update_media_asset(
    asset_id: int,
    payload: MediaAssetUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> MediaAssetRead:
    item = AssetService(db).update_asset(current_admin.id, asset_id, payload.model_dump(exclude_unset=True))
    return MediaAssetRead.model_validate(item)
