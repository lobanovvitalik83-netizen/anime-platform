from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from app.core.config import settings
from app.schemas.public_lookup import PublicLookupResponse
from app.services.yandex_disk_storage_service import YandexDiskStorageService


@dataclass(slots=True)
class MediaPayload:
    data: bytes
    filename: str
    mime_type: str
    asset_type: str


class MediaDeliveryService:
    def resolve_payload(self, result: PublicLookupResponse) -> MediaPayload | None:
        if not result.has_media:
            return None
        if result.asset_type not in {"image", "poster"}:
            return None

        direct_url = self._resolve_direct_url(result)
        if not direct_url:
            return None

        request = Request(
            direct_url,
            headers={
                "User-Agent": "CodeCinemaBot/1.0",
                "Accept": "image/*,application/octet-stream;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=20) as response:
            data = response.read()
            content_type = (response.headers.get_content_type() or "").strip().lower()

        if not data:
            return None

        mime_type = self._normalize_mime_type(content_type or result.mime_type)
        filename = self._build_filename(result, mime_type)
        return MediaPayload(
            data=data,
            filename=filename,
            mime_type=mime_type,
            asset_type=result.asset_type or "image",
        )

    def _resolve_direct_url(self, result: PublicLookupResponse) -> str | None:
        if result.storage_provider == "yandex_disk" and result.storage_object_key:
            return YandexDiskStorageService().get_download_href(result.storage_object_key)
        if result.external_url:
            if result.external_url.startswith("http://") or result.external_url.startswith("https://"):
                return result.external_url
            if settings.public_base_url:
                return urljoin(settings.public_base_url + "/", result.external_url.lstrip("/"))
        return None

    def _normalize_mime_type(self, mime_type: str | None) -> str:
        value = (mime_type or "").split(";")[0].strip().lower()
        if value in {"image/jpeg", "image/png", "image/webp"}:
            return value
        return "image/jpeg"

    def _build_filename(self, result: PublicLookupResponse, mime_type: str) -> str:
        ext = mimetypes.guess_extension(mime_type) or ".jpg"
        asset_id = result.asset_id or 0
        return f"card_{asset_id}{ext}"
