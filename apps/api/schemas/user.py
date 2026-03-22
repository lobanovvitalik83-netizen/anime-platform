from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from schemas.permission import PermissionRead
from schemas.role import RoleRead


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    role_slugs: list[str] = []
    permission_keys: list[str] = []


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None
    role_slugs: list[str] | None = None
    permission_keys: list[str] | None = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    roles: list[RoleRead] = []
    permissions: list[PermissionRead] = []

    model_config = {"from_attributes": True}
