import asyncio
import mimetypes
from dataclasses import dataclass
from html import escape
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from aiogram.types import BufferedInputFile

from app.schemas.public_lookup import PublicLookupResponse


@dataclass(slots=True)
class TelegramResolvedMedia:
    kind: str
    payload: str | BufferedInputFile


class TelegramMediaService:
    def __init__(self, timeout: int = 12):
        self.timeout = timeout

    async def resolve(self, result: PublicLookupResponse) -> TelegramResolvedMedia | None:
        if result.asset_type not in {"image", "poster", "video"}:
            return None

        if result.telegram_file_id:
            return TelegramResolvedMedia(kind=result.asset_type, payload=result.telegram_file_id)

        if not result.external_url:
            return None

        file_bytes, content_type = await asyncio.to_thread(self._download_media, result.external_url)
        filename = self._build_filename(result, content_type)
        return TelegramResolvedMedia(
            kind=result.asset_type,
            payload=BufferedInputFile(file_bytes=file_bytes, filename=filename),
        )

    def _download_media(self, url: str) -> tuple[bytes, str | None]:
        request = Request(
            url,
            headers={
                "User-Agent": "CodeCinemaBot/1.0",
                "Accept": "image/*,video/*,application/octet-stream;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=self.timeout) as response:
            return response.read(), response.headers.get_content_type()

    def _build_filename(self, result: PublicLookupResponse, content_type: str | None) -> str:
        parsed = urlparse(result.external_url or "")
        suffix = ""
        if parsed.path:
            suffix = parsed.path.rsplit("/", 1)[-1]
            if "." in suffix:
                suffix = "." + suffix.rsplit(".", 1)[-1][:10]
            else:
                suffix = ""

        if not suffix:
            suffix = mimetypes.guess_extension(content_type or result.mime_type or "") or (
                ".mp4" if result.asset_type == "video" else ".jpg"
            )

        base = str(result.asset_id or result.code or "media")
        safe_base = "".join(ch for ch in base if ch.isalnum() or ch in {"-", "_"}) or "media"
        return f"{safe_base}{suffix}"


def build_plain_lookup_text(result: PublicLookupResponse) -> str:
    lines: list[str] = []
    if result.title:
        lines.append(result.title)
    if result.genre:
        lines.append(f"Жанр: {result.genre}")
    if result.season_number is not None:
        lines.append(f"Сезон: {result.season_number}")
    if result.episode_number is not None:
        lines.append(f"Серия: {result.episode_number}")
    lines.append("")
    lines.append(f"Код: {result.code}")
    return "\n".join(lines).strip()
