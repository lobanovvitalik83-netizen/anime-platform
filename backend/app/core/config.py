from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Anime Platform API"
    app_env: str = "production"
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./anime_platform.db"

    jwt_secret_key: str = "change_this_to_a_long_random_secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "Anime Platform"

    frontend_reset_url: str = "http://localhost:3000/reset-password"

    owner_email: str = "owner@example.com"
    owner_username: str = "owner"
    owner_password: str = "ChangeThisOwnerPassword123!"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
