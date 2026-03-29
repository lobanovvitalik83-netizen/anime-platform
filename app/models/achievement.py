from sqlalchemy import Index, String, Text, Boolean
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
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon_emoji: Mapped[str | None] = mapped_column(String(16), nullable=True)
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    grants = relationship("AdminAchievement", back_populates="achievement", cascade="all, delete-orphan")
