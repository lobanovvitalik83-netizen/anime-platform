from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class MediaTitle(TimestampMixin, Base):
    __tablename__ = "media_titles"
    __table_args__ = (
        Index("ix_media_titles_type", "type"),
        Index("ix_media_titles_status", "status"),
        Index("ix_media_titles_title", "title"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)

    seasons = relationship("MediaSeason", back_populates="title", cascade="all, delete-orphan")
    episodes = relationship("MediaEpisode", back_populates="title", cascade="all, delete-orphan")
    assets = relationship("MediaAsset", back_populates="title", cascade="all, delete-orphan")
    access_codes = relationship("AccessCode", back_populates="title")
