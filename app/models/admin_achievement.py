from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class AdminAchievement(TimestampMixin, Base):
    __tablename__ = "admin_achievements"
    __table_args__ = (
        Index("ix_admin_achievements_admin_id", "admin_id"),
        Index("ix_admin_achievements_achievement_id", "achievement_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id", ondelete="CASCADE"), nullable=False)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    granted_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    grant_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)

    admin = relationship("Admin", foreign_keys=[admin_id])
    granted_by_admin = relationship("Admin", foreign_keys=[granted_by_admin_id])
    achievement = relationship("Achievement", back_populates="grants")
