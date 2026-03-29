from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.chat_message import ChatMessage
from app.models.chat_participant import ChatParticipant
from app.models.chat_room import ChatRoom


class ChatRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_chats(self) -> list[ChatRoom]:
        statement = select(ChatRoom).options(
            selectinload(ChatRoom.participants).selectinload(ChatParticipant.admin),
            selectinload(ChatRoom.messages).selectinload(ChatMessage.admin),
        ).order_by(ChatRoom.updated_at.desc())
        return list(self.session.scalars(statement).unique())

    def get_chat(self, chat_id: int) -> ChatRoom | None:
        statement = select(ChatRoom).where(ChatRoom.id == chat_id).options(
            selectinload(ChatRoom.participants).selectinload(ChatParticipant.admin),
            selectinload(ChatRoom.messages).selectinload(ChatMessage.admin),
        )
        return self.session.scalar(statement)

    def create_chat(self, title: str, created_by_admin_id: int | None) -> ChatRoom:
        entity = ChatRoom(title=title, created_by_admin_id=created_by_admin_id)
        self.session.add(entity)
        self.session.flush()
        return entity

    def add_participant(self, chat_id: int, admin_id: int) -> ChatParticipant:
        entity = ChatParticipant(chat_id=chat_id, admin_id=admin_id)
        self.session.add(entity)
        self.session.flush()
        return entity

    def create_message(self, chat_id: int, admin_id: int | None, content: str) -> ChatMessage:
        entity = ChatMessage(chat_id=chat_id, admin_id=admin_id, content=content)
        self.session.add(entity)
        self.session.flush()
        return entity
