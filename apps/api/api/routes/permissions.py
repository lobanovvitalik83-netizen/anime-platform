from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from crud.permission import list_permissions
from deps import get_db
from schemas import PermissionRead

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("", response_model=list[PermissionRead])
def permissions_list(db: Session = Depends(get_db)):
    return list_permissions(db)
