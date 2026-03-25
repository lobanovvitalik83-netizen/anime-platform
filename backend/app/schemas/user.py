from pydantic import BaseModel, EmailStr, Field

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
