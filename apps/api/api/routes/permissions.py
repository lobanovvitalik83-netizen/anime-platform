from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from crud.permission import list_permissions
from deps import get_current_user, get_db
from models import User
from schemas import PermissionRead

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("", response_model=list[PermissionRead])
def permissions_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_permissions(db)
