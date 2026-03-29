from pydantic import BaseModel, Field

from app.schemas.common import TimestampReadMixin


class MediaSeasonCreate(BaseModel):
    title_id: int
    season_number: int = Field(ge=1)
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None


class MediaSeasonUpdate(BaseModel):
    season_number: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None


class MediaSeasonRead(TimestampReadMixin):
    id: int
    title_id: int
    season_number: int
    name: str | None
    description: str | None
