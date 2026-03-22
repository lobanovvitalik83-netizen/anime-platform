from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Anime Platform API"
    APP_ENV: str = "production"
    APP_DEBUG: bool = False

    DATABASE_URL: str
    REDIS_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    FIRST_OWNER_EMAIL: str = "owner@example.com"
    FIRST_OWNER_USERNAME: str = "owner"
    FIRST_OWNER_PASSWORD: str = "ChangeThisOwnerPassword123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
