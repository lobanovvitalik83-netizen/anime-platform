from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Permission, User
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = int(payload.get("sub"))
    except Exception:
        raise credentials_exception

    user = db.get(User, user_id)
    if not user:
        raise credentials_exception
    return user


def require_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")
    return current_user


def require_superuser(current_user: User = Depends(require_active_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser required")
    return current_user


def collect_permissions(user: User) -> set[str]:
    result: set[str] = set()
    for role in user.roles:
        for permission in role.permissions:
            result.add(permission.key)
    return result


def require_permission(permission_key: str):
    def checker(current_user: User = Depends(require_active_user)) -> User:
        if current_user.is_superuser:
            return current_user
        permissions = collect_permissions(current_user)
        if permission_key not in permissions:
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission_key}")
        return current_user

    return checker
