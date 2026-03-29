from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Achievement(TimestampMixin, Base):
    __tablename__ = "achievements"
    __table_args__ = (
        Index("ix_achievements_title", "title"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    grants = relationship("AdminAchievement", back_populates="achievement", cascade="all, delete-orphan")
