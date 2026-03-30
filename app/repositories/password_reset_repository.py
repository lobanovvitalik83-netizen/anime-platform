from datetime import datetime

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

    def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash).options(joinedload(PasswordResetToken.admin))
        return self.session.scalar(stmt)

    def mark_used(self, entity: PasswordResetToken) -> PasswordResetToken:
        entity.used_at = datetime.utcnow()
        self.session.flush()
        return entity
