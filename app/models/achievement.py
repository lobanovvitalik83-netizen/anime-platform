from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Achievement(TimestampMixin, Base):
    __tablename__ = "achievements"
    __table_args__ = (
        Index("ix_achievements_title", "title"),
        Index("ix_achievements_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(20), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)

    created_by_admin = relationship("Admin")
    grants = relationship("AdminAchievement", back_populates="achievement", cascade="all, delete-orphan")
