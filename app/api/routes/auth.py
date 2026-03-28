from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.config import settings
from app.core.database import SessionLocal, get_db_session
from app.core.exceptions import AuthenticationError
from app.core.security import create_session_token
from app.models.admin import Admin
from app.schemas.admin import AdminRead
from app.schemas.auth import LoginRequest
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=60 * 60 * 24 * 7,
        secure=settings.session_cookie_secure,
        httponly=settings.session_cookie_httponly,
        samesite=settings.session_cookie_samesite,
        path="/",
    )


@router.post("/login", response_model=AdminRead)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db_session)) -> AdminRead:
    service = AuthService(db)
    try:
        admin = service.authenticate(payload.username, payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    token = create_session_token(admin.id)
    _set_session_cookie(response, token)
    return AdminRead.model_validate(admin)


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response) -> MessageResponse:
    response.delete_cookie(key=settings.session_cookie_name, path="/")
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=AdminRead)
def me(current_admin: Admin = Depends(get_current_admin)) -> AdminRead:
    return AdminRead.model_validate(current_admin)


@router.post("/bootstrap-default-admin", response_model=AdminRead)
def bootstrap_default_admin() -> AdminRead:
    with SessionLocal() as session:
        service = AuthService(session)
        admin = service.ensure_default_admin(
            username=settings.admin_default_username,
            password=settings.admin_default_password,
        )
        if not admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Default admin credentials are not configured")
        return AdminRead.model_validate(admin)
