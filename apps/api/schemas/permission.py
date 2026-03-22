from pydantic import BaseModel


class PermissionRead(BaseModel):
    id: int
    key: str
    description: str | None = None

    model_config = {"from_attributes": True}
