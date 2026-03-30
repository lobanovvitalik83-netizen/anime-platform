from pydantic import BaseModel, Field, model_validator

from app.schemas.common import TimestampReadMixin


class AccessCodeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    title_id: int | None = None
    season_id: int | None = None
    episode_id: int | None = None
    status: str = Field(default="active", min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_target(self):
        if not any([self.title_id, self.season_id, self.episode_id]):
            raise ValueError("At least one of title_id, season_id or episode_id must be provided")
        if not self.code.isdigit():
            raise ValueError("Code must contain digits only")
        return self


class AccessCodeGenerateRequest(BaseModel):
    quantity: int = Field(ge=1, le=1000)
    title_id: int | None = None
    season_id: int | None = None
    episode_id: int | None = None
    status: str = Field(default="active", min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_target(self):
        if not any([self.title_id, self.season_id, self.episode_id]):
            raise ValueError("At least one of title_id, season_id or episode_id must be provided")
        return self


class AccessCodeRead(TimestampReadMixin):
    id: int
    code: str
    title_id: int | None
    season_id: int | None
    episode_id: int | None
    status: str
    created_by_admin_id: int | None
