from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_permission
from app.models import Role, User
from app.schemas import UserCreate, UserOut, UserUpdate
from app.security import hash_password

router = APIRouter()


def user_to_out(user: User) -> UserOut:
    permission_map = {}
    for role in user.roles:
        for permission in role.permissions:
            permission_map[permission.id] = permission
    return UserOut.model_validate(
        {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "roles": user.roles,
            "permissions": list(permission_map.values()),
        }
    )


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(require_permission("users.view"))):
    users = list(db.scalars(select(User).order_by(User.id)).unique().all())
    return [user_to_out(user) for user in users]


@router.post("", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _=Depends(require_permission("users.create"))):
    existing = db.scalar(select(User).where((User.email == payload.email) | (User.username == payload.username)))
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        is_active=True,
        is_superuser=False,
    )
    if payload.role_ids:
        user.roles = list(db.scalars(select(Role).where(Role.id.in_(payload.role_ids))).all())

    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_out(user)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), _=Depends(require_permission("users.view"))):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_out(user)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), _=Depends(require_permission("users.update"))):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.email is not None:
        user.email = payload.email
    if payload.username is not None:
        user.username = payload.username
    if payload.password:
        user.password_hash = hash_password(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role_ids is not None:
        user.roles = list(db.scalars(select(Role).where(Role.id.in_(payload.role_ids))).all())

    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_out(user)
