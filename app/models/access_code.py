from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class AccessCode(TimestampMixin, Base):
    __tablename__ = "access_codes"
    __table_args__ = (
        Index("ix_access_codes_code", "code", unique=True),
        Index("ix_access_codes_status", "status"),
        Index("ix_access_codes_title_id", "title_id"),
        Index("ix_access_codes_season_id", "season_id"),
        Index("ix_access_codes_episode_id", "episode_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title_id: Mapped[int | None] = mapped_column(ForeignKey("media_titles.id", ondelete="SET NULL"), nullable=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("media_seasons.id", ondelete="SET NULL"), nullable=True)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("media_episodes.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    created_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)

    title = relationship("MediaTitle", back_populates="access_codes")
    season = relationship("MediaSeason", back_populates="access_codes")
    episode = relationship("MediaEpisode", back_populates="access_codes")
    created_by_admin = relationship("Admin", back_populates="access_codes")
