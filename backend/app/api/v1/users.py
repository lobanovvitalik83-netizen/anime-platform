from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import require_permission
from app.db.session import get_db
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserUpdate
from app.services.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])

def serialize_user(user: User) -> dict:
    permissions = {}
    for role in user.roles:
        for permission in role.permissions:
            permissions[permission.id] = permission
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at.isoformat() + "Z" if user.created_at else None,
        "updated_at": user.updated_at.isoformat() + "Z" if user.updated_at else None,
        "roles": user.roles,
        "permissions": list(permissions.values()),
    }

@router.get("")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_permission("users.view"))):
    return [serialize_user(user) for user in db.query(User).order_by(User.id.asc()).all()]

@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("users.create"))):
    if db.query(User).filter((User.email == payload.email) | (User.username == payload.username)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email or username already exists")
    roles = db.query(Role).filter(Role.id.in_(payload.role_ids)).all() if payload.role_ids else []
    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        is_active=True,
        is_superuser=False,
        roles=roles,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_user(user)

@router.patch("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("users.update"))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.email is not None:
        user.email = payload.email
    if payload.username is not None:
        user.username = payload.username
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role_ids is not None:
        user.roles = db.query(Role).filter(Role.id.in_(payload.role_ids)).all() if payload.role_ids else []
    db.commit()
    db.refresh(user)
    return serialize_user(user)
