from pydantic import BaseModel

class PermissionOut(BaseModel):
    id: int
    key: str
    description: str

    model_config = {"from_attributes": True}
