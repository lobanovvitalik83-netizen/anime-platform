from app.schemas.common import TimestampReadMixin


class AdminRead(TimestampReadMixin):
    id: int
    username: str
    role: str
    is_active: bool
    full_name: str | None = None
    position: str | None = None
    about: str | None = None
    avatar_url: str | None = None
