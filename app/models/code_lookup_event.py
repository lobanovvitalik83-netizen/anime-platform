from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class CodeLookupEvent(TimestampMixin, Base):
    __tablename__ = "code_lookup_events"
    __table_args__ = (
        Index("ix_code_lookup_events_code_value", "code_value"),
        Index("ix_code_lookup_events_is_found", "is_found"),
        Index("ix_code_lookup_events_source", "source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code_value: Mapped[str] = mapped_column(String(64), nullable=False)
    access_code_id: Mapped[int | None] = mapped_column(ForeignKey("access_codes.id", ondelete="SET NULL"), nullable=True)
    title_id: Mapped[int | None] = mapped_column(ForeignKey("media_titles.id", ondelete="SET NULL"), nullable=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("media_seasons.id", ondelete="SET NULL"), nullable=True)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("media_episodes.id", ondelete="SET NULL"), nullable=True)
    is_found: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="public_api", nullable=False)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
