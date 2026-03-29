from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class ChatParticipant(TimestampMixin, Base):
    __tablename__ = "chat_participants"
    __table_args__ = (
        PrimaryKeyConstraint("chat_id", "admin_id", name="pk_chat_participants"),
    )

    chat_id: Mapped[int] = mapped_column(ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id", ondelete="CASCADE"), nullable=False)

    chat = relationship("ChatRoom", back_populates="participants")
    admin = relationship("Admin")
