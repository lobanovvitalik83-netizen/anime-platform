from fastapi import Request
from starlette.responses import RedirectResponse

from app.core.config import settings
from app.core.security import create_session_token, verify_session_token
from app.models.admin import Admin
from app.repositories.admin_repository import AdminRepository


ROLE_LEVELS = {
    "editor": 1,
    "admin": 2,
    "superadmin": 3,
}


def has_required_role(admin: Admin | None, min_role: str = "editor") -> bool:
    if not admin:
        return False
    return ROLE_LEVELS.get(admin.role, 0) >= ROLE_LEVELS.get(min_role, 1)


def get_current_admin_from_request(request: Request, db) -> Admin | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None

    payload = verify_session_token(token)
    if not payload:
        return None

    admin = AdminRepository(db).get_by_id(payload["admin_id"])
    if not admin or not admin.is_active:
        return None

    return admin


def redirect_to_login() -> RedirectResponse:
    return RedirectResponse(url="/admin/login", status_code=303)


def redirect_to(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


def set_auth_cookie(response: RedirectResponse, admin_id: int) -> None:
    token = create_session_token(admin_id)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=60 * 60 * 24 * 7,
        secure=settings.session_cookie_secure,
        httponly=settings.session_cookie_httponly,
        samesite=settings.session_cookie_samesite,
        path="/",
    )


def clear_auth_cookie(response: RedirectResponse) -> None:
    response.delete_cookie(key=settings.session_cookie_name, path="/")
