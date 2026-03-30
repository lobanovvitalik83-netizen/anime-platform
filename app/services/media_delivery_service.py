import mimetypes
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.repositories.media_asset_repository import MediaAssetRepository
from app.schemas.public_lookup import PublicLookupResponse
from app.services.yandex_disk_storage_service import YandexDiskStorageService

logger = get_logger(__name__)

_IMAGE_ASSET_TYPES = {'image', 'poster'}


@dataclass(slots=True)
class MediaPayload:
    file_bytes: bytes
    file_name: str
    mime_type: str | None
    asset_type: str | None


class MediaDeliveryService:
    def __init__(self, session: Session | None = None):
        self.session = session

    def resolve_media_payload(self, result: PublicLookupResponse) -> MediaPayload | None:
        if result.asset_type not in _IMAGE_ASSET_TYPES:
            return None

        asset = self._get_asset(result.asset_id)
        if asset is not None:
            payload = self._resolve_payload_from_asset(asset)
            if payload is not None:
                return payload

        url = self.resolve_media_url(result)
        if not url:
            return None
        return self._download_payload(url, mime_type=result.mime_type, asset_type=result.asset_type)

    def resolve_media_url(self, result: PublicLookupResponse) -> str | None:
        if result.external_url:
            return self._normalize_url(result.external_url)

        asset = self._get_asset(result.asset_id)
        if asset is None:
            return None

        if getattr(asset, 'storage_provider', None) == 'yandex_disk' and asset.id:
            return self._build_proxy_url(asset.id)

        raw_external_url = getattr(asset, 'external_url', None)
        if raw_external_url:
            return self._normalize_url(raw_external_url)
        return None

    def _get_asset(self, asset_id: int | None):
        if not asset_id or self.session is None:
            return None
        return MediaAssetRepository(self.session).get_by_id(asset_id)

    def _resolve_payload_from_asset(self, asset) -> MediaPayload | None:
        download_url: str | None = None

        if getattr(asset, 'storage_provider', None) == 'yandex_disk' and getattr(asset, 'storage_object_key', None):
            try:
                download_url = YandexDiskStorageService().get_download_href(asset.storage_object_key)
            except Exception as exc:
                logger.warning('Failed to resolve Yandex Disk href for asset_id=%s: %s', asset.id, exc)

        if not download_url and getattr(asset, 'external_url', None):
            download_url = self._normalize_url(asset.external_url)

        if not download_url:
            proxy_url = self._build_proxy_url(getattr(asset, 'id', None))
            if proxy_url:
                download_url = proxy_url

        if not download_url:
            return None

        return self._download_payload(
            download_url,
            mime_type=getattr(asset, 'mime_type', None),
            asset_type=getattr(asset, 'asset_type', None),
        )

    def _build_proxy_url(self, asset_id: int | None) -> str | None:
        if not asset_id or not settings.public_base_url:
            return None
        return f"{settings.public_base_url}/media/yandex-disk/{asset_id}"

    def _normalize_url(self, value: str) -> str | None:
        raw = (value or '').strip()
        if not raw:
            return None
        if raw.startswith('http://') or raw.startswith('https://'):
            return raw
        if raw.startswith('/') and settings.public_base_url:
            return urljoin(f'{settings.public_base_url}/', raw.lstrip('/'))
        return None

    def _download_payload(self, url: str, *, mime_type: str | None, asset_type: str | None) -> MediaPayload | None:
        try:
            request = Request(url, headers={'User-Agent': 'MediaBridgeBot/1.0'})
            with urlopen(request, timeout=60) as response:
                file_bytes = response.read()
                content_type = response.headers.get('Content-Type') or mime_type or 'application/octet-stream'
        except Exception as exc:
            logger.warning('Failed to download media from %s: %s', url, exc)
            return None

        if not file_bytes:
            return None

        clean_mime = (content_type or mime_type or 'application/octet-stream').split(';', 1)[0].strip().lower()
        file_name = self._build_file_name(url=url, mime_type=clean_mime, asset_type=asset_type)
        return MediaPayload(
            file_bytes=file_bytes,
            file_name=file_name,
            mime_type=clean_mime,
            asset_type=asset_type,
        )

    def _build_file_name(self, *, url: str, mime_type: str | None, asset_type: str | None) -> str:
        path = urlparse(url).path
        candidate = Path(path).name or ''
        if candidate and '.' in candidate:
            return candidate[:128]

        extension = ''
        if mime_type:
            extension = mimetypes.guess_extension(mime_type) or ''
        if not extension:
            extension = '.jpg' if asset_type in _IMAGE_ASSET_TYPES else '.bin'
        base_name = 'media' if asset_type in _IMAGE_ASSET_TYPES else 'file'
        return f'{base_name}{extension}'
