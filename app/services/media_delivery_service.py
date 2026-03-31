import asyncio
import json
import mimetypes
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib import parse as urllib_parse
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from aiogram.types import BufferedInputFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.models.media_asset import MediaAsset
from app.repositories.media_asset_repository import MediaAssetRepository
from app.schemas.public_lookup import PublicLookupResponse
from app.services.yandex_disk_storage_service import YandexDiskStorageService


@dataclass
class ResolvedMedia:
    asset: MediaAsset | None
    source_url: str | None
    file_bytes: bytes
    file_name: str
    mime_type: str | None
    asset_type: str | None


class MediaDeliveryService:
    def __init__(self, session: Session | None = None):
        self.session = session
        self.assets = MediaAssetRepository(session) if session is not None else None

    async def resolve_for_telegram(self, result: PublicLookupResponse) -> ResolvedMedia | None:
        return await asyncio.to_thread(self.resolve_media, result)

    def resolve_media(self, result: PublicLookupResponse) -> ResolvedMedia | None:
        asset = self._get_asset(result)
        source_url = self._resolve_source_url(result, asset)
        if not source_url:
            return None
        file_bytes, mime_type, final_url = self._download_bytes(source_url)
        file_name = self._build_file_name(result=result, asset=asset, source_url=final_url, mime_type=mime_type)
        return ResolvedMedia(
            asset=asset,
            source_url=final_url,
            file_bytes=file_bytes,
            file_name=file_name,
            mime_type=mime_type or result.mime_type,
            asset_type=(asset.asset_type if asset else result.asset_type),
        )

    def build_telegram_input_file(self, media: ResolvedMedia) -> BufferedInputFile:
        return BufferedInputFile(media.file_bytes, filename=media.file_name)

    def persist_telegram_file_id(self, asset_id: int | None, telegram_file_id: str | None) -> None:
        if self.session is None or self.assets is None or not asset_id or not telegram_file_id:
            return
        asset = self.assets.get_by_id(asset_id)
        if not asset:
            return
        if asset.telegram_file_id == telegram_file_id:
            return
        asset.telegram_file_id = telegram_file_id
        self.session.commit()
        self.session.refresh(asset)

    def _get_asset(self, result: PublicLookupResponse) -> MediaAsset | None:
        if self.assets is None or not result.asset_id:
            return None
        return self.assets.get_by_id(result.asset_id)

    def _resolve_source_url(self, result: PublicLookupResponse, asset: MediaAsset | None) -> str | None:
        if asset and asset.storage_provider == 'yandex_disk' and asset.storage_object_key:
            return YandexDiskStorageService().get_download_href(asset.storage_object_key)
        if result.external_url:
            return self._absolutize_url(result.external_url)
        if asset and asset.external_url:
            return self._absolutize_url(asset.external_url)
        return None

    def _absolutize_url(self, url: str) -> str:
        value = (url or '').strip()
        if not value:
            return value
        if value.startswith('http://') or value.startswith('https://'):
            return value
        base = settings.public_base_url
        if not base:
            raise ValidationError('PUBLIC_BASE_URL не настроен для относительных media URL.')
        return urllib_parse.urljoin(base + '/', value.lstrip('/'))

    def _download_bytes(self, url: str) -> tuple[bytes, str | None, str]:
        request = urllib_request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (MediaBridgeBot/1.0)',
                'Accept': '*/*',
            },
        )
        try:
            with urllib_request.urlopen(request, timeout=30) as response:
                file_bytes = response.read()
                if not file_bytes:
                    raise ValidationError('Пустой ответ при загрузке медиа.')
                mime_type = response.headers.get_content_type()
                final_url = response.geturl()
                return file_bytes, mime_type, final_url
        except HTTPError as exc:
            body = exc.read().decode('utf-8', errors='ignore')
            raise ValidationError(f'Не удалось загрузить медиа: HTTP {exc.code} {body or exc.reason}') from exc
        except URLError as exc:
            raise ValidationError(f'Не удалось загрузить медиа: {exc.reason}') from exc

    def _build_file_name(
        self,
        *,
        result: PublicLookupResponse,
        asset: MediaAsset | None,
        source_url: str,
        mime_type: str | None,
    ) -> str:
        parsed = urllib_parse.urlparse(source_url)
        name = Path(parsed.path).name
        if not name or '.' not in name:
            suffix = mimetypes.guess_extension(mime_type or result.mime_type or '') or ''
            prefix = 'video' if (asset.asset_type if asset else result.asset_type) == 'video' else 'image'
            name = f'{prefix}-{result.asset_id or uuid.uuid4().hex}{suffix}'
        return name[:200]

    def upload_vk_photo_and_get_attachment(self, *, peer_id: int, file_bytes: bytes, file_name: str) -> str:
        upload_server = self._vk_api_call(
            'photos.getMessagesUploadServer',
            {'peer_id': peer_id},
        )
        upload_url = upload_server.get('upload_url')
        if not upload_url:
            raise ValidationError('VK не вернул upload_url для изображения.')

        uploaded = self._vk_upload_photo(upload_url=upload_url, file_bytes=file_bytes, file_name=file_name)
        saved_items = self._vk_api_call(
            'photos.saveMessagesPhoto',
            {
                'photo': uploaded.get('photo', ''),
                'server': uploaded.get('server', ''),
                'hash': uploaded.get('hash', ''),
            },
        )
        if not saved_items:
            raise ValidationError('VK не сохранил изображение.')
        photo = saved_items[0]
        owner_id = photo.get('owner_id')
        photo_id = photo.get('id')
        access_key = photo.get('access_key')
        if owner_id is None or photo_id is None:
            raise ValidationError('VK вернул неполный photo attachment.')
        attachment = f'photo{owner_id}_{photo_id}'
        if access_key:
            attachment = f'{attachment}_{access_key}'
        return attachment

    def _vk_upload_photo(self, *, upload_url: str, file_bytes: bytes, file_name: str) -> dict:
        boundary = f'----MediaBridge{uuid.uuid4().hex}'
        content_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
        body = self._build_multipart_body(boundary=boundary, file_name=file_name, file_bytes=file_bytes, content_type=content_type)
        request = urllib_request.Request(
            upload_url,
            data=body,
            headers={
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'Content-Length': str(len(body)),
                'User-Agent': 'Mozilla/5.0 (MediaBridgeBot/1.0)',
            },
            method='POST',
        )
        try:
            with urllib_request.urlopen(request, timeout=60) as response:
                raw = response.read().decode('utf-8')
        except HTTPError as exc:
            body = exc.read().decode('utf-8', errors='ignore')
            raise ValidationError(f'VK upload failed: HTTP {exc.code} {body or exc.reason}') from exc
        data = json.loads(raw)
        if data.get('error'):
            raise ValidationError(f"VK upload failed: {data['error']}")
        return data

    def _build_multipart_body(self, *, boundary: str, file_name: str, file_bytes: bytes, content_type: str) -> bytes:
        boundary_bytes = boundary.encode('utf-8')
        chunks = [
            b'--' + boundary_bytes + b'\r\n',
            f'Content-Disposition: form-data; name="photo"; filename="{file_name}"\r\n'.encode('utf-8'),
            f'Content-Type: {content_type}\r\n\r\n'.encode('utf-8'),
            file_bytes,
            b'\r\n--' + boundary_bytes + b'--\r\n',
        ]
        return b''.join(chunks)

    def _vk_api_call(self, method: str, params: dict) -> dict | list:
        token = settings.vk_bot_token.strip()
        if not token:
            raise ValidationError('VK_BOT_TOKEN не настроен.')
        payload = {
            **params,
            'access_token': token,
            'v': settings.vk_api_version,
        }
        data = urllib_parse.urlencode(payload).encode('utf-8')
        request = urllib_request.Request(f'https://api.vk.com/method/{method}', data=data, method='POST')
        with urllib_request.urlopen(request, timeout=30) as response:
            raw = response.read().decode('utf-8')
        parsed = json.loads(raw)
        if 'error' in parsed:
            error = parsed['error']
            raise ValidationError(f"VK API error: {error.get('error_msg', 'unknown error')}")
        return parsed.get('response')
