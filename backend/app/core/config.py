from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    app_name: str = "Anime Platform API"
    app_env: str = "production"
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = f"sqlite:///{BASE_DIR / 'anime_platform.db'}"

    jwt_secret_key: str = "change_this_to_a_very_long_random_secret_key_2026"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    owner_email: str = "owner@example.com"
    owner_username: str = "owner"
    owner_password: str = "ChangeThisOwnerPassword123!"

    frontend_reset_url: str = "http://localhost:3000/reset-password"

    telegram_bot_enabled: bool = True
    telegram_bot_username: str = ""
    telegram_admin_chat_id: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
