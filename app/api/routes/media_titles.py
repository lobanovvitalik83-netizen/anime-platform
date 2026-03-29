from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db_session
from app.models.admin import Admin
from app.schemas.media_title import MediaTitleCreate, MediaTitleRead, MediaTitleUpdate
from app.services.media_service import MediaService

router = APIRouter(prefix="/api/media-titles", tags=["media-titles"])


@router.get("", response_model=list[MediaTitleRead])
def list_media_titles(
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> list[MediaTitleRead]:
    items = MediaService(db).list_titles()
    return [MediaTitleRead.model_validate(item) for item in items]


@router.post("", response_model=MediaTitleRead)
def create_media_title(
    payload: MediaTitleCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> MediaTitleRead:
    item = MediaService(db).create_title(current_admin.id, payload.model_dump())
    return MediaTitleRead.model_validate(item)


@router.get("/{title_id}", response_model=MediaTitleRead)
def get_media_title(
    title_id: int,
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> MediaTitleRead:
    item = MediaService(db).get_title(title_id)
    return MediaTitleRead.model_validate(item)


@router.patch("/{title_id}", response_model=MediaTitleRead)
def update_media_title(
    title_id: int,
    payload: MediaTitleUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> MediaTitleRead:
    item = MediaService(db).update_title(current_admin.id, title_id, payload.model_dump(exclude_unset=True))
    return MediaTitleRead.model_validate(item)
