from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.repositories.admin_notification_repository import AdminNotificationRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.import_job_repository import ImportJobRepository
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository

logger = get_logger(__name__)


class SystemHardeningService:
    def __init__(self, session: Session):
        self.session = session
        self.notifications = AdminNotificationRepository(session)
        self.audit_logs = AuditLogRepository(session)
        self.import_jobs = ImportJobRepository(session)
        self.reset_tokens = PasswordResetTokenRepository(session)

    def run_startup_cleanup(self) -> dict[str, int]:
        stats = {
            'notifications_purged': self.notifications.purge_older_than(settings.notifications_retention_days),
            'audit_logs_purged': self.audit_logs.purge_older_than(settings.audit_retention_days),
            'import_jobs_purged': self.import_jobs.purge_older_than(settings.import_jobs_retention_days),
            'password_reset_tokens_purged': self.reset_tokens.expire_older_than(settings.password_reset_token_ttl_hours // 24 + 7),
        }
        self.session.commit()
        logger.info('System cleanup completed: %s', stats)
        return stats
