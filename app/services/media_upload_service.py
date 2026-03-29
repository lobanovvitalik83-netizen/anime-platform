import mimetypes
from contextlib import suppress

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BufferedInputFile

from app.core.config import settings
from app.core.exceptions import ValidationError


class MediaUploadService:
    async def upload_uploaded_file(
        self,
        file_bytes: bytes,
        file_name: str,
        content_type: str | None,
        asset_type: str,
    ) -> dict:
        if not settings.telegram_bot_token:
            raise ValidationError("TELEGRAM_BOT_TOKEN is not configured")

        chat_id = settings.resolved_media_upload_chat_id
        if not chat_id:
            raise ValidationError("TELEGRAM_MEDIA_UPLOAD_CHAT_ID is not configured")

        detected_mime = (content_type or mimetypes.guess_type(file_name)[0] or "").lower().strip()
        if not detected_mime:
            raise ValidationError("Cannot detect uploaded file MIME type")

        normalized_asset_type = asset_type.strip().lower()
        is_video = normalized_asset_type == "video" or detected_mime.startswith("video/")
        is_image = normalized_asset_type in {"image", "poster"} or detected_mime.startswith("image/")

        if not is_video and not is_image:
            raise ValidationError("Only image/poster/video uploads are supported")

        if is_image:
            if detected_mime not in settings.allowed_image_mime:
                raise ValidationError(f"Unsupported image MIME type: {detected_mime}")
            if len(file_bytes) > settings.max_image_size_bytes:
                raise ValidationError("Image file is too large")
        if is_video:
            if detected_mime not in settings.allowed_video_mime:
                raise ValidationError(f"Unsupported video MIME type: {detected_mime}")
            if len(file_bytes) > settings.max_video_size_bytes:
                raise ValidationError("Video file is too large")

        bot = Bot(
            token=settings.telegram_bot_token,
            default=DefaultBotProperties(parse_mode="HTML"),
        )
        try:
            input_file = BufferedInputFile(file=file_bytes, filename=file_name)

            if is_video:
                message = await bot.send_video(
                    chat_id=chat_id,
                    video=input_file,
                    caption="media upload",
                )
                file_id = message.video.file_id
                asset_type_result = "video"
            else:
                message = await bot.send_photo(
                    chat_id=chat_id,
                    photo=input_file,
                    caption="media upload",
                )
                file_id = message.photo[-1].file_id
                asset_type_result = "image" if normalized_asset_type != "poster" else "poster"

            with suppress(Exception):
                await bot.delete_message(chat_id=chat_id, message_id=message.message_id)

            return {
                "storage_kind": "telegram_file_id",
                "telegram_file_id": file_id,
                "external_url": None,
                "mime_type": detected_mime,
                "asset_type": asset_type_result,
            }
        finally:
            await bot.session.close()
