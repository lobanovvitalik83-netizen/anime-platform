from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Admin(TimestampMixin, Base):
    __tablename__ = "admins"
    __table_args__ = (
        Index("ix_admins_username", "username"),
        Index("ix_admins_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="admin", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    full_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    position: Mapped[str | None] = mapped_column(String(150), nullable=True)
    about: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extra_permissions: Mapped[str | None] = mapped_column(Text, nullable=True)

    access_codes = relationship("AccessCode", back_populates="created_by_admin")
    audit_logs = relationship("AuditLog", back_populates="admin")
    import_jobs = relationship("ImportJob", back_populates="admin")

    achievement_grants = relationship("AdminAchievement", foreign_keys="AdminAchievement.admin_id", back_populates="admin", cascade="all, delete-orphan")
