from sqlalchemy import BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class ReportTicket(TimestampMixin, Base):
    __tablename__ = "report_tickets"
    __table_args__ = (
        Index("ix_report_tickets_status", "status"),
        Index("ix_report_tickets_tg_user_id", "tg_user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tg_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tg_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tg_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_message_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)

    assigned_admin = relationship("Admin")
    messages = relationship("ReportMessage", back_populates="ticket", cascade="all, delete-orphan")
