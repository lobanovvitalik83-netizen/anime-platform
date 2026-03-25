from datetime import datetime, timedelta
from secrets import token_urlsafe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, PasswordResetToken
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.user import UserOut
from app.services.emailer import send_reset_email
from app.services.security import verify_password, create_access_token, create_refresh_token, decode_token, hash_password

router = APIRouter(prefix="/auth", tags=["auth"])

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

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter((User.email == payload.email_or_username) | (User.username == payload.email_or_username)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect login or password")
    return TokenResponse(access_token=create_access_token(str(user.id)), refresh_token=create_refresh_token(str(user.id)))

@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        user_id = int(decode_token(payload.refresh_token, "refresh"))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return TokenResponse(access_token=create_access_token(str(user.id)), refresh_token=create_refresh_token(str(user.id)))

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        return {"status": "ok"}
    token = token_urlsafe(32)
    record = PasswordResetToken(user_id=user.id, token=token, expires_at=datetime.utcnow() + timedelta(hours=1), used=False)
    db.add(record)
    db.commit()
    reset_url = f"{settings.frontend_reset_url}?token={token}"
    try:
        send_reset_email(user.email, reset_url)
        return {"status": "ok", "delivery": "email"}
    except RuntimeError:
        return {"status": "ok", "delivery": "manual", "reset_token": token, "reset_url": reset_url}

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    record = db.query(PasswordResetToken).filter(PasswordResetToken.token == payload.token, PasswordResetToken.used == False).first()
    if not record or record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token is invalid or expired")
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.password_hash = hash_password(payload.new_password[:72])
    record.used = True
    db.commit()
    return {"status": "ok"}
