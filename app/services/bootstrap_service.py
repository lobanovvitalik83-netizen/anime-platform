from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.auth_service import AuthService
from app.services.system_hardening_service import SystemHardeningService

logger = get_logger(__name__)


def ensure_default_admin_exists() -> None:
    with SessionLocal() as session:
        AuthService(session).ensure_default_admin()


def run_startup_hardening() -> None:
    with SessionLocal() as session:
        try:
            SystemHardeningService(session).run_startup_cleanup()
        except Exception:
            logger.exception("Startup hardening cleanup failed")
            session.rollback()
