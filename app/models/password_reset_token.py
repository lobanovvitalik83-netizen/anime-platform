from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class PasswordResetToken(TimestampMixin, Base):
    __tablename__ = 'password_reset_tokens'
    __table_args__ = (
        Index('ix_password_reset_tokens_token_hash', 'token_hash'),
        Index('ix_password_reset_tokens_target_admin_id', 'target_admin_id'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    target_admin_id: Mapped[int] = mapped_column(ForeignKey('admins.id', ondelete='CASCADE'), nullable=False)
    created_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey('admins.id', ondelete='SET NULL'), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    target_admin = relationship('Admin', foreign_keys=[target_admin_id])
    created_by_admin = relationship('Admin', foreign_keys=[created_by_admin_id])
