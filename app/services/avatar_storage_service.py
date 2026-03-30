import mimetypes
import secrets

from app.core.config import settings
from app.core.exceptions import ValidationError


class AvatarStorageService:
    def save_avatar(
        self,
        *,
        admin_id: int,
        file_bytes: bytes,
        file_name: str,
        content_type: str | None,
        old_avatar_url: str | None = None,
    ) -> str:
        detected_mime = (content_type or mimetypes.guess_type(file_name)[0] or "").lower().strip()
        if detected_mime not in settings.allowed_image_mime:
            raise ValidationError("Для аватара поддерживаются только image/jpeg, image/png, image/webp.")
        if len(file_bytes) > settings.max_avatar_size_bytes:
            raise ValidationError("Аватар слишком большой.")

        extension_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
        extension = extension_map.get(detected_mime, ".bin")
        token = secrets.token_hex(8)
        filename = f"admin_{admin_id}_{token}{extension}"

        settings.avatar_upload_dir.mkdir(parents=True, exist_ok=True)
        target_path = settings.avatar_upload_dir / filename
        target_path.write_bytes(file_bytes)

        if old_avatar_url and old_avatar_url.startswith("/uploads/avatars/"):
            old_name = old_avatar_url.rsplit("/", 1)[-1]
            old_path = settings.avatar_upload_dir / old_name
            if old_path.exists():
                old_path.unlink()

        return f"/uploads/avatars/{filename}"
