from pydantic import BaseModel

class ContentOut(BaseModel):
    id: int
    title: str
    description: str
    tags: str
    media_type: str
    media_path: str | None = None
    status: str
    visibility: str
    is_archived: bool
    created_at: str | None = None
    updated_at: str | None = None

class ContentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    tags: str | None = None
    status: str | None = None
    visibility: str | None = None
    is_archived: bool | None = None
