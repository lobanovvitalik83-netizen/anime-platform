import re
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Media Bridge", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=3000, alias="APP_PORT")
    app_secret_key: str = Field(alias="APP_SECRET_KEY")
    app_log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")

    database_url: str = Field(alias="DATABASE_URL")

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_bot_username: str = Field(default="", alias="TELEGRAM_BOT_USERNAME")
    telegram_media_upload_chat_id: str = Field(default="", alias="TELEGRAM_MEDIA_UPLOAD_CHAT_ID")

    admin_default_username: str = Field(default="admin", alias="ADMIN_DEFAULT_USERNAME")
    admin_default_password: str = Field(default="", alias="ADMIN_DEFAULT_PASSWORD")

    session_cookie_name: str = Field(default="media_bridge_session", alias="SESSION_COOKIE_NAME")
    session_cookie_secure: bool = Field(default=False, alias="SESSION_COOKIE_SECURE")
    session_cookie_httponly: bool = Field(default=True, alias="SESSION_COOKIE_HTTPONLY")
    session_cookie_samesite: str = Field(default="lax", alias="SESSION_COOKIE_SAMESITE")

    code_length: int = Field(default=8, alias="CODE_LENGTH")

    allowed_image_mime_raw: str = Field(default="image/jpeg,image/png,image/webp", alias="ALLOWED_IMAGE_MIME")
    allowed_video_mime_raw: str = Field(default="video/mp4", alias="ALLOWED_VIDEO_MIME")
    max_image_size_bytes: int = Field(default=5_242_880, alias="MAX_IMAGE_SIZE_BYTES")
    max_video_size_bytes: int = Field(default=52_428_800, alias="MAX_VIDEO_SIZE_BYTES")

    data_dir_raw: str = Field(default="/app/data", alias="DATA_DIR")
    max_avatar_size_bytes: int = Field(default=2_097_152, alias="MAX_AVATAR_SIZE_BYTES")

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        value = value.lower().strip()
        if value not in {"development", "production", "test"}:
            raise ValueError("APP_ENV must be development, production or test")
        return value

    @field_validator("app_log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        value = value.upper().strip()
        if value not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("Invalid APP_LOG_LEVEL")
        return value

    @field_validator("session_cookie_samesite")
    @classmethod
    def validate_samesite(cls, value: str) -> str:
        value = value.lower().strip()
        if value not in {"lax", "strict", "none"}:
            raise ValueError("Invalid SESSION_COOKIE_SAMESITE")
        return value

    @field_validator("code_length")
    @classmethod
    def validate_code_length(cls, value: int) -> int:
        if value < 4 or value > 32:
            raise ValueError("CODE_LENGTH must be between 4 and 32")
        return value

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def allowed_image_mime(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_image_mime_raw.split(",") if item.strip()}

    @property
    def allowed_video_mime(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_video_mime_raw.split(",") if item.strip()}

    @property
    def resolved_media_upload_chat_id(self):
        value = self.telegram_media_upload_chat_id.strip()
        if not value:
            return None
        if re.fullmatch(r"-?\d+", value):
            return int(value)
        return value

    @property
    def data_dir(self) -> Path:
        return Path(self.data_dir_raw)

    @property
    def public_upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def avatar_upload_dir(self) -> Path:
        return self.public_upload_dir / "avatars"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
