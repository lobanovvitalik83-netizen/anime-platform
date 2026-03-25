from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_active_user
from app.models import Permission

router = APIRouter()


@router.get("")
def list_permissions(db: Session = Depends(get_db), _=Depends(require_active_user)):
    return list(db.scalars(select(Permission).order_by(Permission.key)).all())
