
from sqlalchemy import BigInteger, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class ReportMessage(TimestampMixin, Base):
    __tablename__ = "report_messages"
    __table_args__ = (
        Index("ix_report_messages_ticket_id", "ticket_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("report_tickets.id", ondelete="CASCADE"), nullable=False)
    direction: Mapped[str] = mapped_column(Text, nullable=False)
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    tg_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    ticket = relationship("ReportTicket", back_populates="messages")
    admin = relationship("Admin")
