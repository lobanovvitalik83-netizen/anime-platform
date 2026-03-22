from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.user import create_user, get_user_by_id, list_users, update_user
from deps import get_db
from schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def users_list(db: Session = Depends(get_db)):
    return list_users(db)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def users_create(payload: UserCreate, db: Session = Depends(get_db)):
    return create_user(
        db,
        email=payload.email,
        username=payload.username,
        password=payload.password,
        role_slugs=payload.role_slugs,
        permission_keys=payload.permission_keys,
    )


@router.get("/{user_id}", response_model=UserRead)
def users_get(user_id: int, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def users_update(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return update_user(
        db,
        user=user,
        email=payload.email,
        username=payload.username,
        password=payload.password,
        is_active=payload.is_active,
        role_slugs=payload.role_slugs,
        permission_keys=payload.permission_keys,
    )
