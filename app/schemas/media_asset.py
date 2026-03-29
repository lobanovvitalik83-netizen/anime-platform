from pydantic import BaseModel, Field, model_validator

from app.schemas.common import TimestampReadMixin


class MediaAssetCreate(BaseModel):
    title_id: int | None = None
    season_id: int | None = None
    episode_id: int | None = None
    asset_type: str = Field(min_length=1, max_length=50)
    storage_kind: str = Field(min_length=1, max_length=50)
    telegram_file_id: str | None = Field(default=None, max_length=255)
    external_url: str | None = Field(default=None, max_length=2048)
    mime_type: str | None = Field(default=None, max_length=255)
    is_primary: bool = False

    @model_validator(mode="after")
    def validate_entity(self):
        if not any([self.title_id, self.season_id, self.episode_id]):
            raise ValueError("At least one owner must be provided")
        if self.storage_kind == "telegram_file_id" and not self.telegram_file_id:
            raise ValueError("telegram_file_id is required for storage_kind=telegram_file_id")
        if self.storage_kind == "external_url" and not self.external_url:
            raise ValueError("external_url is required for storage_kind=external_url")
        return self


class MediaAssetUpdate(BaseModel):
    asset_type: str | None = Field(default=None, min_length=1, max_length=50)
    storage_kind: str | None = Field(default=None, min_length=1, max_length=50)
    telegram_file_id: str | None = Field(default=None, max_length=255)
    external_url: str | None = Field(default=None, max_length=2048)
    mime_type: str | None = Field(default=None, max_length=255)
    is_primary: bool | None = None


class MediaAssetRead(TimestampReadMixin):
    id: int
    title_id: int | None
    season_id: int | None
    episode_id: int | None
    asset_type: str
    storage_kind: str
    telegram_file_id: str | None
    external_url: str | None
    mime_type: str | None
    is_primary: bool
