from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.core.database import get_db_session
from app.repositories.media_asset_repository import MediaAssetRepository
from app.services.yandex_disk_storage_service import YandexDiskStorageService

router = APIRouter(include_in_schema=False)


@router.get("/media/yandex-disk/{asset_id}")
def proxy_yandex_disk_asset(asset_id: int, db: Session = Depends(get_db_session)):
    asset = MediaAssetRepository(db).get_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.storage_provider != "yandex_disk" or not asset.storage_object_key:
        raise HTTPException(status_code=404, detail="Yandex Disk asset not found")

    href = YandexDiskStorageService().get_download_href(asset.storage_object_key)
    return RedirectResponse(url=href, status_code=307)
