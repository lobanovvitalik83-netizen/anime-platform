from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class MediaEpisode(TimestampMixin, Base):
    __tablename__ = "media_episodes"
    __table_args__ = (
        UniqueConstraint("season_id", "episode_number", name="uq_media_episodes_season_episode_number"),
        Index("ix_media_episodes_title_id", "title_id"),
        Index("ix_media_episodes_season_id", "season_id"),
        Index("ix_media_episodes_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("media_titles.id", ondelete="CASCADE"), nullable=False)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("media_seasons.id", ondelete="SET NULL"), nullable=True)
    episode_number: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)

    title = relationship("MediaTitle", back_populates="episodes")
    season = relationship("MediaSeason", back_populates="episodes")
    assets = relationship("MediaAsset", back_populates="episode", cascade="all, delete-orphan")
    access_codes = relationship("AccessCode", back_populates="episode")
