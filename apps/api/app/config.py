from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Anime Platform API"
    app_env: str = "production"
    app_debug: bool = False

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    owner_email: str = "owner@example.com"
    owner_username: str = "owner"
    owner_password: str = "ChangeThisOwnerPassword123!"

    media_root: str = "/storage/media"


settings = Settings()
