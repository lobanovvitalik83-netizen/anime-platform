from pydantic import BaseModel, Field

from schemas.permission import PermissionRead


class RoleBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class RoleCreate(RoleBase):
    permission_keys: list[str] = []


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    slug: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    permission_keys: list[str] | None = None


class RoleRead(RoleBase):
    id: int
    permissions: list[PermissionRead] = []

    model_config = {"from_attributes": True}
