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
    telegram_help_contact_text: str = Field(default="", alias="TELEGRAM_HELP_CONTACT")

    media_storage_backend_raw: str = Field(default="auto", alias="MEDIA_STORAGE_BACKEND")
    public_base_url_raw: str = Field(default="", alias="PUBLIC_BASE_URL")

    s3_endpoint_url: str = Field(default="", alias="S3_ENDPOINT_URL")
    s3_access_key_id: str = Field(default="", alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str = Field(default="", alias="S3_SECRET_ACCESS_KEY")
    s3_bucket_name: str = Field(default="", alias="S3_BUCKET_NAME")
    s3_region: str = Field(default="", alias="S3_REGION")
    s3_public_base_url_raw: str = Field(default="", alias="S3_PUBLIC_BASE_URL")
    s3_key_prefix_raw: str = Field(default="media-bridge", alias="S3_KEY_PREFIX")

    yandex_disk_oauth_token: str = Field(default="", alias="YANDEX_DISK_OAUTH_TOKEN")
    yandex_disk_base_path_raw: str = Field(default="app:/media-bridge", alias="YANDEX_DISK_BASE_PATH")

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

    login_rate_limit_attempts: int = Field(default=7, alias="LOGIN_RATE_LIMIT_ATTEMPTS")
    login_rate_limit_window_seconds: int = Field(default=300, alias="LOGIN_RATE_LIMIT_WINDOW_SECONDS")
    report_rate_limit_attempts: int = Field(default=6, alias="REPORT_RATE_LIMIT_ATTEMPTS")
    report_rate_limit_window_seconds: int = Field(default=120, alias="REPORT_RATE_LIMIT_WINDOW_SECONDS")
    maintenance_allow_health: bool = Field(default=True, alias="MAINTENANCE_ALLOW_HEALTH")
    audit_retention_days: int = Field(default=120, alias="AUDIT_RETENTION_DAYS")
    notifications_retention_days: int = Field(default=45, alias="NOTIFICATIONS_RETENTION_DAYS")
    import_jobs_retention_days: int = Field(default=30, alias="IMPORT_JOBS_RETENTION_DAYS")
    max_bulk_delete_items: int = Field(default=50, alias="MAX_BULK_DELETE_ITEMS")

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
    def media_storage_backend(self) -> str:
        value = (self.media_storage_backend_raw or "auto").strip().lower()
        if value not in {"auto", "s3", "yandex_disk"}:
            return "auto"
        return value

    @property
    def public_base_url(self) -> str:
        value = self.public_base_url_raw.strip()
        return value.rstrip("/") if value else ""

    @property
    def s3_public_base_url(self) -> str:
        value = self.s3_public_base_url_raw.strip()
        return value.rstrip("/") if value else ""

    @property
    def s3_key_prefix(self) -> str:
        value = (self.s3_key_prefix_raw or "").strip().strip("/")
        return value

    @property
    def s3_configured(self) -> bool:
        return bool(self.s3_bucket_name.strip() and self.s3_access_key_id.strip() and self.s3_secret_access_key.strip())

    @property
    def yandex_disk_configured(self) -> bool:
        return bool(self.yandex_disk_oauth_token.strip())

    @property
    def yandex_disk_base_path(self) -> str:
        value = (self.yandex_disk_base_path_raw or "app:/media-bridge").strip()
        if value.startswith("app:/") or value.startswith("disk:/"):
            return value.rstrip("/")
        value = value.strip("/")
        return f"app:/{value}" if value else "app:/media-bridge"

    @property
    def data_dir(self) -> Path:
        return Path(self.data_dir_raw)

    @property
    def public_upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def avatar_upload_dir(self) -> Path:
        return self.public_upload_dir / "avatars"

    @property
    def media_upload_enabled(self) -> bool:
        backend = self.media_storage_backend
        if backend == "yandex_disk":
            return self.yandex_disk_configured
        if backend == "s3":
            return self.s3_configured
        return self.yandex_disk_configured or self.s3_configured

    @property
    def media_storage_backend_label(self) -> str:
        backend = self.media_storage_backend
        if backend == "yandex_disk":
            return "Yandex Disk"
        if backend == "s3":
            return "S3-compatible external storage"
        if self.yandex_disk_configured:
            return "Yandex Disk"
        if self.s3_configured:
            return "S3-compatible external storage"
        return "external storage is not configured"

    @property
    def media_upload_help_text(self) -> str:
        backend = self.media_storage_backend
        if backend == "yandex_disk":
            if self.yandex_disk_configured:
                return "Файлы карточек загружаются сразу на Яндекс Диск. BotHost хранит только metadata."
            return "Для режима yandex_disk нужно заполнить YANDEX_DISK_OAUTH_TOKEN."
        if backend == "s3":
            if self.s3_configured:
                return "Файлы карточек загружаются сразу во внешний S3-compatible storage."
            return "Для режима s3 нужно заполнить S3_* переменные."
        if self.yandex_disk_configured:
            return "Auto mode выбрал Yandex Disk. Файлы карточек грузятся в папку приложения на Диске."
        if self.s3_configured:
            return "Auto mode выбрал S3-compatible storage."
        return "Внешний storage не настроен. Сохранять можно только прямые внешние ссылки."


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
