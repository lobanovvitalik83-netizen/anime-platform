from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from crud.permission import get_permissions_by_keys
from crud.role import get_roles_by_slugs
from models import User
from security import hash_password, verify_password


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id.asc())).all())


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email_or_username(db: Session, email: str, username: str) -> User | None:
    return db.scalar(select(User).where(or_(User.email == email, User.username == username)))


def get_user_by_login(db: Session, email_or_username: str) -> User | None:
    return db.scalar(select(User).where(or_(User.email == email_or_username, User.username == email_or_username)))


def authenticate_user(db: Session, email_or_username: str, password: str) -> User | None:
    user = get_user_by_login(db, email_or_username)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user(
    db: Session,
    *,
    email: str,
    username: str,
    password: str,
    role_slugs: list[str],
    permission_keys: list[str],
    is_superuser: bool = False,
) -> User:
    existing = get_user_by_email_or_username(db, email=email, username=username)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with same email or username already exists")

    user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
        is_active=True,
        is_superuser=is_superuser,
    )
    user.roles = get_roles_by_slugs(db, role_slugs)
    user.permissions = get_permissions_by_keys(db, permission_keys)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    *,
    user: User,
    email: str | None = None,
    username: str | None = None,
    password: str | None = None,
    is_active: bool | None = None,
    role_slugs: list[str] | None = None,
    permission_keys: list[str] | None = None,
) -> User:
    if email is not None:
        user.email = email
    if username is not None:
        user.username = username
    if password is not None:
        user.password_hash = hash_password(password)
    if is_active is not None:
        user.is_active = is_active
    if role_slugs is not None:
        user.roles = get_roles_by_slugs(db, role_slugs)
    if permission_keys is not None:
        user.permissions = get_permissions_by_keys(db, permission_keys)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
