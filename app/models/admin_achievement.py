from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class AdminAchievement(TimestampMixin, Base):
    """
    Model representing the link between a staff member (admin) and an achievement they have been
    granted. Historically this model used a ``reason`` column to store the explanation for
    granting the achievement. In more recent iterations the field was renamed to
    ``grant_reason`` and an ordering integer ``display_order`` was added. To support both
    database schemas (with or without a ``reason`` column), we define ``grant_reason`` as the
    primary text column and alias ``reason`` to it via ``synonym``.  If your database still
    contains a ``reason`` column, SQLAlchemy will map ``grant_reason`` to that column by
    explicitly specifying the column name.
    """

    __tablename__ = "admin_achievements"
    __table_args__ = (
        Index("ix_admin_achievements_admin_id", "admin_id"),
        Index("ix_admin_achievements_achievement_id", "achievement_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id", ondelete="CASCADE"), nullable=False)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    # Use the ``reason`` column if it exists in the DB, otherwise fall back to creating a
    # ``grant_reason`` column. The ``key`` argument defines the mapped attribute name and the
    # first argument defines the column name in the database.  If your database schema still
    # uses the legacy ``reason`` column, this mapping will point ``grant_reason`` at that
    # column.  If you have migrated to a new schema, the column will be created as
    # ``grant_reason``.
    grant_reason: Mapped[str | None] = mapped_column(
        "reason",  # database column name
        Text,
        key="grant_reason",
        nullable=True,
    )
    # A small integer used to control the order in which achievements are displayed.  This
    # defaults to zero for backwards compatibility with schemas that do not have the
    # ``display_order`` column.
    display_order: Mapped[int] = mapped_column(default=0)
    granted_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)

    # Create a synonym so that existing code referring to ``reason`` continues to work.  The
    # synonym maps the attribute name ``reason`` to the underlying ``grant_reason`` attribute.
    # See https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.synonym for details.
    from sqlalchemy.orm import synonym  # type: ignore
    reason = synonym("grant_reason")

    admin = relationship("Admin", foreign_keys=[admin_id])
    granted_by_admin = relationship("Admin", foreign_keys=[granted_by_admin_id])
    achievement = relationship("Achievement")
