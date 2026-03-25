from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    description: str


class RoleBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None


class RoleOut(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    permissions: List[PermissionOut] = []


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str
    role_ids: List[int] = []


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role_ids: Optional[List[int]] = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    roles: List[RoleOut] = []
    permissions: List[PermissionOut] = []


class LoginRequest(BaseModel):
    email_or_username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ContentCreate(BaseModel):
    title: str
    description: str = ""
    tags: List[str] = []
    status: str = "draft"
    visibility: str = "public"


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    visibility: Optional[str] = None


class ContentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    tags: List[str]
    media_type: Optional[str]
    media_path: Optional[str]
    status: str
    visibility: str
    created_at: datetime
    updated_at: datetime


class SettingItem(BaseModel):
    key: str
    value: str


class SettingUpdate(BaseModel):
    items: List[SettingItem]


class AnalyticsSummary(BaseModel):
    users_total: int
    roles_total: int
    permissions_total: int
    content_total: int
    content_published: int
    content_draft: int
    content_archived: int


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str
