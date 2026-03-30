import mimetypes
import secrets
from pathlib import Path

import boto3

from app.core.config import settings
from app.core.exceptions import ValidationError


class ExternalMediaStorageService:
    def build_storage_key(self, *, file_name: str, asset_type: str) -> str:
        guessed_extension = Path(file_name).suffix or mimetypes.guess_extension(mimetypes.guess_type(file_name)[0] or "") or ""
        safe_ext = guessed_extension[:12] if guessed_extension else ""
        token = secrets.token_hex(12)
        folder = "video" if asset_type == "video" else "image"
        prefix = settings.s3_key_prefix
        return f"{prefix}/{folder}/{token}{safe_ext}" if prefix else f"{folder}/{token}{safe_ext}"

    def upload_s3(self, *, file_bytes: bytes, file_name: str, content_type: str | None, asset_type: str) -> dict:
        if not settings.s3_configured:
            raise ValidationError("S3-compatible storage не настроен.")

        key = self.build_storage_key(file_name=file_name, asset_type=asset_type)
        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region or None,
        )
        client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=key,
            Body=file_bytes,
            ContentType=content_type or mimetypes.guess_type(file_name)[0] or "application/octet-stream",
        )

        if settings.s3_public_base_url:
            external_url = f"{settings.s3_public_base_url}/{key}"
        elif settings.s3_endpoint_url:
            external_url = f"{settings.s3_endpoint_url.rstrip('/')}/{settings.s3_bucket_name}/{key}"
        else:
            external_url = f"/external-media/{key}"

        return {
            "storage_kind": "external_url",
            "storage_provider": "s3",
            "storage_object_key": key,
            "external_url": external_url,
            "telegram_file_id": None,
            "mime_type": content_type or mimetypes.guess_type(file_name)[0],
            "asset_type": asset_type,
            "uploaded_by_system": True,
        }

    def delete_managed_asset(self, asset) -> None:
        if not asset or not getattr(asset, "uploaded_by_system", False):
            return
        if getattr(asset, "storage_provider", None) != "s3":
            return
        object_key = getattr(asset, "storage_object_key", None)
        if not object_key:
            return
        if not settings.s3_configured:
            return

        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region or None,
        )
        client.delete_object(Bucket=settings.s3_bucket_name, Key=object_key)
