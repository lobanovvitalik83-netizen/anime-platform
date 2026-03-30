from app.core.database import SessionLocal
from app.services.auth_service import AuthService


def ensure_default_admin_exists() -> None:
    with SessionLocal() as session:
        AuthService(session).ensure_default_admin()
