from pydantic import BaseModel
from app.schemas.permission import PermissionOut

class RoleOut(BaseModel):
    id: int
    name: str
    slug: str | None = None
    description: str | None = None
    permissions: list[PermissionOut] = []
    model_config = {"from_attributes": True}
