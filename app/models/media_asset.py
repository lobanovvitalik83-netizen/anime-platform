from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class MediaAsset(TimestampMixin, Base):
    __tablename__ = "media_assets"
    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN title_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN season_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN episode_id IS NOT NULL THEN 1 ELSE 0 END) >= 1",
            name="media_assets_at_least_one_owner",
        ),
        CheckConstraint(
            "(storage_kind = 'telegram_file_id' AND telegram_file_id IS NOT NULL) OR "
            "(storage_kind = 'external_url' AND external_url IS NOT NULL)",
            name="media_assets_storage_kind_payload_match",
        ),
        Index("ix_media_assets_title_id", "title_id"),
        Index("ix_media_assets_season_id", "season_id"),
        Index("ix_media_assets_episode_id", "episode_id"),
        Index("ix_media_assets_asset_type", "asset_type"),
        Index("ix_media_assets_is_primary", "is_primary"),
        Index("ix_media_assets_storage_provider", "storage_provider"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title_id: Mapped[int | None] = mapped_column(ForeignKey("media_titles.id", ondelete="CASCADE"), nullable=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("media_seasons.id", ondelete="CASCADE"), nullable=True)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("media_episodes.id", ondelete="CASCADE"), nullable=True)

    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    telegram_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    storage_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    storage_object_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_by_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    title = relationship("MediaTitle", back_populates="assets")
    season = relationship("MediaSeason", back_populates="assets")
    episode = relationship("MediaEpisode", back_populates="assets")
