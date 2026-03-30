from pydantic import BaseModel


class PublicLookupResponse(BaseModel):
    code: str
    title_id: int | None
    title: str | None
    original_title: str | None
    genre: str | None
    title_type: str | None
    title_status: str | None
    year: int | None
    season_id: int | None
    season_number: int | None
    season_name: str | None
    episode_id: int | None
    episode_number: int | None
    episode_name: str | None
    episode_status: str | None
    description: str | None
    asset_id: int | None
    asset_type: str | None
    storage_kind: str | None
    telegram_file_id: str | None
    external_url: str | None
    mime_type: str | None
    storage_provider: str | None = None
    storage_object_key: str | None = None
    has_media: bool
