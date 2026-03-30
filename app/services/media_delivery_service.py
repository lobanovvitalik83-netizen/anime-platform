import mimetypes
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.schemas.public_lookup import PublicLookupResponse
from app.services.yandex_disk_storage_service import YandexDiskStorageService


@dataclass
class DeliveredMedia:
    file_name: str
    content_type: str
    file_bytes: bytes
    asset_type: str


class MediaDeliveryService:
    def fetch_lookup_media(self, result: PublicLookupResponse) -> DeliveredMedia | None:
        if not result.has_media:
            return None
        if result.storage_kind == "telegram_file_id":
            return None
        if result.storage_kind != "external_url" or not result.external_url:
            return None

        if result.asset_type not in {"image", "poster", "video"}:
            return None

        source_url = self._resolve_download_url(result)
        request = Request(source_url, headers={"User-Agent": settings.app_name})
        try:
            with urlopen(request, timeout=60) as response:
                body = response.read()
                content_type = (response.headers.get_content_type() or "application/octet-stream").lower().strip()
        except (HTTPError, URLError) as exc:
            raise ValidationError(f"Не удалось загрузить медиа для отправки: {exc}") from exc

        if not body:
            raise ValidationError("Источник медиа вернул пустой файл.")

        extension = mimetypes.guess_extension(content_type) or self._extension_from_url(source_url) or (".mp4" if result.asset_type == "video" else ".jpg")
        prefix = "video" if result.asset_type == "video" else "image"
        file_name = f"lookup_{result.code}_{prefix}{extension}"
        return DeliveredMedia(file_name=file_name, content_type=content_type, file_bytes=body, asset_type=result.asset_type)

    def _resolve_download_url(self, result: PublicLookupResponse) -> str:
        if result.storage_provider == "yandex_disk" and result.storage_object_key:
            return YandexDiskStorageService().get_download_href(result.storage_object_key)
        return result.external_url or ""

    @staticmethod
    def _extension_from_url(url: str) -> str | None:
        suffix = Path(url.split("?", 1)[0]).suffix.lower().strip()
        return suffix or None


class VKMediaUploader:
    api_base = "https://api.vk.com/method"

    def __init__(self):
        if not settings.vk_bot_token:
            raise ValidationError("VK_BOT_TOKEN не настроен.")

    def upload_for_peer(self, *, peer_id: int, media: DeliveredMedia) -> str:
        if media.asset_type in {"image", "poster"}:
            return self._upload_photo(peer_id=peer_id, media=media)
        return self._upload_doc(peer_id=peer_id, media=media)

    def _api_call(self, method: str, payload: dict, *, use_post: bool = True) -> dict:
        full_payload = {**payload, "access_token": settings.vk_bot_token, "v": settings.vk_api_version}
        data = urlencode(full_payload).encode("utf-8") if use_post else None
        url = f"{self.api_base}/{method}"
        if not use_post:
            url = f"{url}?{urlencode(full_payload)}"
        request = Request(url, data=data, method="POST" if use_post else "GET")
        with urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw)
        if "error" in parsed:
            raise ValidationError(f"VK API error: {parsed['error'].get('error_msg', 'unknown error')}")
        return parsed.get("response") or {}

    def _multipart_body(self, field_name: str, file_name: str, content_type: str, body: bytes) -> tuple[bytes, str]:
        boundary = f"----WebKitFormBoundary{settings.app_name.replace(' ', '')}"
        boundary_bytes = boundary.encode("utf-8")
        chunks = [
            b"--" + boundary_bytes + b"\r\n",
            f'Content-Disposition: form-data; name="{field_name}"; filename="{file_name}"\r\n'.encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            body,
            b"\r\n--" + boundary_bytes + b"--\r\n",
        ]
        return b"".join(chunks), boundary

    def _upload_binary(self, upload_url: str, *, field_name: str, media: DeliveredMedia) -> dict:
        payload, boundary = self._multipart_body(field_name, media.file_name, media.content_type, media.file_bytes)
        request = Request(
            upload_url,
            data=payload,
            method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        with urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw)

    def _upload_photo(self, *, peer_id: int, media: DeliveredMedia) -> str:
        server = self._api_call("photos.getMessagesUploadServer", {"peer_id": peer_id}, use_post=False)
        upload_result = self._upload_binary(server["upload_url"], field_name="photo", media=media)
        saved = self._api_call(
            "photos.saveMessagesPhoto",
            {
                "photo": upload_result["photo"],
                "server": upload_result["server"],
                "hash": upload_result["hash"],
            },
        )
        item = saved[0]
        return f"photo{item['owner_id']}_{item['id']}"

    def _upload_doc(self, *, peer_id: int, media: DeliveredMedia) -> str:
        server = self._api_call("docs.getMessagesUploadServer", {"peer_id": peer_id, "type": "doc"}, use_post=False)
        upload_result = self._upload_binary(server["upload_url"], field_name="file", media=media)
        saved = self._api_call("docs.save", {"file": upload_result["file"], "title": media.file_name})
        doc = saved.get("doc") or saved
        return f"doc{doc['owner_id']}_{doc['id']}"
