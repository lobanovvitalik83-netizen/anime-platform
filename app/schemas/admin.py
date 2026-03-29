from app.schemas.common import TimestampReadMixin


class AdminRead(TimestampReadMixin):
    id: int
    username: str
    role: str
    is_active: bool
