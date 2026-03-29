import mimetypes

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.services.external_media_storage_service import ExternalMediaStorageService
from app.services.remote_media_import_service import RemoteMediaImportService


class MediaUploadService:
    def __init__(self):
        self.external_storage = ExternalMediaStorageService()
        self.remote_import = RemoteMediaImportService()

    async def upload_uploaded_file(
        self,
        file_bytes: bytes,
        file_name: str,
        content_type: str | None,
        asset_type: str,
    ) -> dict:
        detected_mime = (content_type or mimetypes.guess_type(file_name)[0] or "").lower().strip()
        if not detected_mime:
            raise ValidationError("Не удалось определить MIME type файла.")

        normalized_result_type = self._validate_payload(
            file_bytes=file_bytes,
            detected_mime=detected_mime,
            asset_type=asset_type,
        )

        if not settings.s3_configured:
            raise ValidationError(
                "Upload файлов отключён: BotHost не хранит медиа, а внешний S3-compatible storage не настроен."
            )

        return self.external_storage.upload_s3(
            file_bytes=file_bytes,
            file_name=file_name,
            content_type=detected_mime,
            asset_type=normalized_result_type,
        )

    async def import_from_remote_url(
        self,
        *,
        source_url: str,
        asset_type: str,
    ) -> dict:
        if not settings.s3_configured:
            raise ValidationError(
                "Импорт по ссылке с копированием в storage отключён: внешний S3-compatible storage не настроен."
            )

        tentative_asset_type = asset_type.strip().lower()
        max_size = settings.max_video_size_bytes if tentative_asset_type == "video" else settings.max_image_size_bytes
        file_bytes, file_name, content_type = self.remote_import.fetch(source_url, max_size_bytes=max_size)
        detected_mime = (content_type or mimetypes.guess_type(file_name)[0] or "").lower().strip()
        normalized_result_type = self._validate_payload(
            file_bytes=file_bytes,
            detected_mime=detected_mime,
            asset_type=asset_type,
        )
        payload = self.external_storage.upload_s3(
            file_bytes=file_bytes,
            file_name=file_name,
            content_type=detected_mime,
            asset_type=normalized_result_type,
        )
        payload["source_url"] = self.remote_import.normalize_url(source_url)
        return payload

    def _validate_payload(self, *, file_bytes: bytes, detected_mime: str, asset_type: str) -> str:
        normalized_asset_type = asset_type.strip().lower()
        is_video = normalized_asset_type == "video" or detected_mime.startswith("video/")
        is_image = normalized_asset_type in {"image", "poster"} or detected_mime.startswith("image/")

        if not is_video and not is_image:
            raise ValidationError("Поддерживаются только image, poster и video.")

        if is_image:
            if detected_mime not in settings.allowed_image_mime:
                raise ValidationError(f"Неподдерживаемый MIME type изображения: {detected_mime}")
            if len(file_bytes) > settings.max_image_size_bytes:
                raise ValidationError("Файл изображения слишком большой.")
        if is_video:
            if detected_mime not in settings.allowed_video_mime:
                raise ValidationError(f"Неподдерживаемый MIME type видео: {detected_mime}")
            if len(file_bytes) > settings.max_video_size_bytes:
                raise ValidationError("Файл видео слишком большой.")

        return "video" if is_video else ("poster" if normalized_asset_type == "poster" else "image")
