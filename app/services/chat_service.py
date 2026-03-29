from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.admin import Admin
from app.repositories.admin_repository import AdminRepository
from app.repositories.chat_repository import ChatRepository
from app.services.audit_service import AuditService


class ChatService:
    def __init__(self, session: Session):
        self.session = session
        self.chats = ChatRepository(session)
        self.admins = AdminRepository(session)
        self.audit = AuditService(session)

    def list_active_admins(self) -> list[Admin]:
        return self.admins.list_active()

    def list_chats_for_admin(self, admin: Admin):
        visible = []
        for chat in self.chats.list_chats():
            participant_ids = {participant.admin_id for participant in chat.participants if participant.admin and participant.admin.is_active}
            if admin.id in participant_ids:
                visible.append(chat)
        return visible

    def get_chat_for_admin(self, admin: Admin, chat_id: int):
        chat = self.chats.get_chat(chat_id)
        if not chat:
            raise NotFoundError("Чат не найден.")
        participant_ids = {participant.admin_id for participant in chat.participants if participant.admin and participant.admin.is_active}
        if admin.id not in participant_ids:
            raise ValidationError("У вас нет доступа к этому чату.")
        return chat

    def create_chat(self, creator: Admin, *, title: str, participant_ids: list[int]):
        title = title.strip()
        if not title:
            raise ValidationError("Название чата обязательно.")

        active_admins = {item.id: item for item in self.admins.list_active()}
        if creator.id not in active_admins:
            raise ValidationError("Создатель чата должен быть активным.")

        unique_ids = {int(item) for item in participant_ids}
        unique_ids.add(creator.id)
        final_ids = [item for item in unique_ids if item in active_admins]
        if len(final_ids) < 2:
            raise ValidationError("Для чата нужно минимум 2 активных участника.")

        chat = self.chats.create_chat(title=title, created_by_admin_id=creator.id)
        for admin_id in final_ids:
            self.chats.add_participant(chat.id, admin_id)

        self.audit.log(admin_id=creator.id, action="create_chat", entity_type="chat_room", entity_id=str(chat.id), payload={"title": chat.title, "participants": final_ids})
        self.session.commit()
        return self.chats.get_chat(chat.id)

    def post_message(self, actor: Admin, chat_id: int, content: str):
        content = content.strip()
        if not content:
            raise ValidationError("Сообщение не может быть пустым.")

        chat = self.get_chat_for_admin(actor, chat_id)
        self.chats.create_message(chat.id, actor.id, content)
        self.audit.log(admin_id=actor.id, action="post_chat_message", entity_type="chat_room", entity_id=str(chat.id), payload={"content": content[:120]})
        self.session.commit()
        return self.chats.get_chat(chat.id)
