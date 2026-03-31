from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from app.core.config import settings


@dataclass(slots=True)
class MediaPayload:
    content: bytes
    filename: str
    content_type: str
    asset_type: str | None


class MediaDeliveryService:
    def resolve_media_payload(
        self,
        *,
        asset_id: int | None,
        external_url: str | None,
        asset_type: str | None,
        mime_type: str | None,
    ) -> MediaPayload | None:
        url = self._resolve_download_url(asset_id=asset_id, external_url=external_url)
        if not url:
            return None

        request = Request(
            url,
            headers={
                "User-Agent": "CodeCinemaBot/1.0",
                "Accept": "*/*",
            },
        )
        with urlopen(request, timeout=25) as response:
            content = response.read()
            response_type = response.headers.get_content_type() or mime_type or "application/octet-stream"
            final_url = response.geturl() or url

        if not content:
            return None

        filename = self._guess_filename(final_url=final_url, asset_type=asset_type, mime_type=response_type)
        return MediaPayload(
            content=content,
            filename=filename,
            content_type=response_type,
            asset_type=asset_type,
        )

    def _resolve_download_url(self, *, asset_id: int | None, external_url: str | None) -> str | None:
        if asset_id and settings.public_base_url:
            return f"{settings.public_base_url}/media/yandex-disk/{asset_id}"
        if not external_url:
            return None
        if external_url.startswith("http://") or external_url.startswith("https://"):
            return external_url
        if settings.public_base_url:
            return urljoin(f"{settings.public_base_url}/", external_url.lstrip("/"))
        return external_url

    def _guess_filename(self, *, final_url: str, asset_type: str | None, mime_type: str | None) -> str:
        parsed = urlparse(final_url)
        raw_name = Path(parsed.path).name or "media"
        base, ext = Path(raw_name).stem, Path(raw_name).suffix
        if not ext:
            guessed = mimetypes.guess_extension(mime_type or "") or self._fallback_extension(asset_type)
            ext = guessed or ""
        safe_base = (base or "media").strip() or "media"
        return f"{safe_base[:80]}{ext}"

    def _fallback_extension(self, asset_type: str | None) -> str:
        if asset_type == "video":
            return ".mp4"
        return ".jpg"
