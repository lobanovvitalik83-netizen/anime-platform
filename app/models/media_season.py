from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class MediaSeason(TimestampMixin, Base):
    __tablename__ = "media_seasons"
    __table_args__ = (
        UniqueConstraint("title_id", "season_number", name="uq_media_seasons_title_season_number"),
        Index("ix_media_seasons_title_id", "title_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("media_titles.id", ondelete="CASCADE"), nullable=False)
    season_number: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    title = relationship("MediaTitle", back_populates="seasons")
    episodes = relationship("MediaEpisode", back_populates="season", cascade="all, delete-orphan")
    assets = relationship("MediaAsset", back_populates="season")
    access_codes = relationship("AccessCode", back_populates="season")
