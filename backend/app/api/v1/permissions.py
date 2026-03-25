from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import require_permission
from app.db.session import get_db
from app.models.user import Permission, User

router = APIRouter(prefix="/permissions", tags=["permissions"])

@router.get("")
def list_permissions(db: Session = Depends(get_db), _: User = Depends(require_permission("permissions.view"))):
    return db.query(Permission).order_by(Permission.id.asc()).all()
