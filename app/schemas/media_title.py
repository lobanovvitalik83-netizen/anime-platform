from pydantic import BaseModel, Field

from app.schemas.common import TimestampReadMixin


class MediaTitleCreate(BaseModel):
    type: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=255)
    original_title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    year: int | None = Field(default=None, ge=1800, le=3000)
    status: str = Field(default="draft", min_length=1, max_length=50)


class MediaTitleUpdate(BaseModel):
    type: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    original_title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    year: int | None = Field(default=None, ge=1800, le=3000)
    status: str | None = Field(default=None, min_length=1, max_length=50)


class MediaTitleRead(TimestampReadMixin):
    id: int
    type: str
    title: str
    original_title: str | None
    description: str | None
    year: int | None
    status: str
