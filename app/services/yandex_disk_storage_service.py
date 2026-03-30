import json
import mimetypes
import secrets
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from app.core.config import settings
from app.core.exceptions import ValidationError


class YandexDiskStorageService:
    api_base_url = "https://cloud-api.yandex.net/v1/disk"

    def __init__(self):
        if not settings.yandex_disk_oauth_token.strip():
            raise ValidationError("YANDEX_DISK_OAUTH_TOKEN не настроен.")

    def build_storage_path(self, *, file_name: str, asset_type: str) -> str:
        guessed_extension = Path(file_name).suffix or mimetypes.guess_extension(mimetypes.guess_type(file_name)[0] or "") or ""
        safe_ext = guessed_extension[:12] if guessed_extension else ""
        token = secrets.token_hex(12)
        folder = "video" if asset_type == "video" else "image"
        return f"{settings.yandex_disk_base_path}/{folder}/{token}{safe_ext}"

    def upload_bytes(self, *, file_bytes: bytes, file_name: str, content_type: str | None, asset_type: str) -> dict:
        storage_path = self.build_storage_path(file_name=file_name, asset_type=asset_type)
        self.ensure_directory(settings.yandex_disk_base_path)
        self.ensure_directory(f"{settings.yandex_disk_base_path}/image")
        self.ensure_directory(f"{settings.yandex_disk_base_path}/video")

        href = self.get_upload_href(storage_path)
        request = Request(
            href,
            data=file_bytes,
            method="PUT",
            headers={
                "Content-Type": content_type or mimetypes.guess_type(file_name)[0] or "application/octet-stream",
            },
        )
        with urlopen(request, timeout=60):
            pass

        return {
            "storage_kind": "external_url",
            "storage_provider": "yandex_disk",
            "storage_object_key": storage_path,
            "external_url": None,
            "telegram_file_id": None,
            "mime_type": content_type or mimetypes.guess_type(file_name)[0],
            "asset_type": asset_type,
            "uploaded_by_system": True,
        }

    def get_download_href(self, storage_path: str) -> str:
        payload = self._request_json(
            method="GET",
            path="/resources/download",
            params={"path": storage_path},
        )
        href = payload.get("href")
        if not href:
            raise ValidationError("Не удалось получить download href из Яндекс Диска.")
        return href

    def delete_path(self, storage_path: str) -> None:
        self._request_no_content(
            method="DELETE",
            path="/resources",
            params={"path": storage_path, "permanently": "true"},
            allow_statuses={202, 204, 404},
        )

    def ensure_directory(self, storage_path: str) -> None:
        self._request_no_content(
            method="PUT",
            path="/resources",
            params={"path": storage_path},
            allow_statuses={201, 409},
        )

    def get_upload_href(self, storage_path: str) -> str:
        payload = self._request_json(
            method="GET",
            path="/resources/upload",
            params={"path": storage_path, "overwrite": "true"},
        )
        href = payload.get("href")
        if not href:
            raise ValidationError("Не удалось получить upload href из Яндекс Диска.")
        return href

    def _request_json(self, *, method: str, path: str, params: dict | None = None) -> dict:
        url = f"{self.api_base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        request = Request(
            url,
            method=method,
            headers={"Authorization": f"OAuth {settings.yandex_disk_oauth_token.strip()}"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise ValidationError(f"Yandex Disk API error {exc.code}: {body or exc.reason}") from exc

    def _request_no_content(self, *, method: str, path: str, params: dict | None = None, allow_statuses: set[int] | None = None) -> None:
        url = f"{self.api_base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        request = Request(
            url,
            method=method,
            headers={"Authorization": f"OAuth {settings.yandex_disk_oauth_token.strip()}"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                if allow_statuses and response.status not in allow_statuses:
                    raise ValidationError(f"Yandex Disk API returned unexpected status {response.status}.")
        except HTTPError as exc:
            if allow_statuses and exc.code in allow_statuses:
                return
            body = exc.read().decode("utf-8", errors="ignore")
            raise ValidationError(f"Yandex Disk API error {exc.code}: {body or exc.reason}") from exc

    def delete_managed_asset(self, asset) -> None:
        if not asset or not getattr(asset, "uploaded_by_system", False):
            return
        if getattr(asset, "storage_provider", None) != "yandex_disk":
            return
        storage_path = getattr(asset, "storage_object_key", None)
        if not storage_path:
            return
        self.delete_path(storage_path)
