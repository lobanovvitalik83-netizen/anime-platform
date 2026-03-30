from pydantic import BaseModel, Field, model_validator

from app.schemas.common import TimestampReadMixin


class MediaEpisodeCreate(BaseModel):
    title_id: int
    season_id: int | None = None
    episode_number: int = Field(ge=1)
    name: str | None = Field(default=None, max_length=255)
    synopsis: str | None = None
    status: str = Field(default="draft", min_length=1, max_length=50)


class MediaEpisodeUpdate(BaseModel):
    season_id: int | None = None
    episode_number: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, max_length=255)
    synopsis: str | None = None
    status: str | None = Field(default=None, min_length=1, max_length=50)


class MediaEpisodeRead(TimestampReadMixin):
    id: int
    title_id: int
    season_id: int | None
    episode_number: int
    name: str | None
    synopsis: str | None
    status: str
