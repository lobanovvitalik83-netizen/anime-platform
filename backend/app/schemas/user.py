from pydantic import BaseModel, EmailStr, Field
from app.schemas.role import RoleOut
from app.schemas.permission import PermissionOut

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=72)
    role_ids: list[int] = []

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    is_active: bool | None = None
    role_ids: list[int] | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool
    is_superuser: bool = False
    created_at: str | None = None
    updated_at: str | None = None
    roles: list[RoleOut] = []
    permissions: list[PermissionOut] = []

    model_config = {"from_attributes": True}
