from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import require_permission
from app.db.session import get_db
from app.models.user import Role, User

router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("")
def list_roles(db: Session = Depends(get_db), _: User = Depends(require_permission("roles.view"))):
    return db.query(Role).order_by(Role.id.asc()).all()
