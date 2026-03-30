from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> PasswordResetToken:
        entity = PasswordResetToken(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None:
        stmt = (
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
            .options(joinedload(PasswordResetToken.target_admin), joinedload(PasswordResetToken.created_by_admin))
        )
        return self.session.scalar(stmt)

    def list_active_for_admin(self, admin_id: int) -> list[PasswordResetToken]:
        stmt = (
            select(PasswordResetToken)
            .where(
                PasswordResetToken.target_admin_id == admin_id,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > datetime.utcnow(),
            )
            .order_by(PasswordResetToken.id.desc())
        )
        return list(self.session.scalars(stmt))

    def mark_used(self, entity: PasswordResetToken) -> PasswordResetToken:
        entity.used_at = datetime.utcnow()
        self.session.flush()
        return entity

    def expire_older_than(self, days: int) -> int:
        if days <= 0:
            return 0
        threshold = datetime.utcnow() - timedelta(days=days)
        rows = self.session.query(PasswordResetToken).filter(PasswordResetToken.created_at < threshold).delete(synchronize_session=False)
        self.session.flush()
        return int(rows or 0)
