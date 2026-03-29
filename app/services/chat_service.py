from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.admin import Admin
from app.repositories.admin_repository import AdminRepository
from app.repositories.chat_repository import ChatRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.site_setting_service import SiteSettingService


class ChatService:
    def __init__(self, session: Session):
        self.session = session
        self.chats = ChatRepository(session)
        self.admins = AdminRepository(session)
        self.audit = AuditService(session)
        self.site_settings = SiteSettingService(session)
        self.notifications = NotificationService(session)

    def list_active_admins(self) -> list[Admin]:
        return self.admins.list_active()

    def messages_enabled(self) -> bool:
        return self.site_settings.is_messages_enabled()

    def ensure_messages_enabled(self) -> None:
        if not self.messages_enabled():
            raise ValidationError("Сообщения временно отключены superadmin.")

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
        self.ensure_messages_enabled()
        title = title.strip()
        if not title:
            raise ValidationError("Название чата обязательно.")
        active_admins = {item.id: item for item in self.admins.list_active()}
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

    def find_direct_chat(self, left_admin_id: int, right_admin_id: int):
        target = {left_admin_id, right_admin_id}
        for chat in self.chats.list_chats():
            participant_ids = {participant.admin_id for participant in chat.participants if participant.admin and participant.admin.is_active}
            if participant_ids == target and len(participant_ids) == 2:
                return chat
        return None

    def get_or_create_direct_chat(self, actor: Admin, target_admin_id: int):
        self.ensure_messages_enabled()
        if actor.id == target_admin_id:
            raise ValidationError("Нельзя открыть диалог с самим собой.")
        target = self.admins.get_by_id(target_admin_id)
        if not target or not target.is_active:
            raise ValidationError("Пользователь недоступен для диалога.")
        existing = self.find_direct_chat(actor.id, target.id)
        if existing:
            return existing
        title = f"{actor.full_name or actor.username} / {target.full_name or target.username}"
        chat = self.chats.create_chat(title=title, created_by_admin_id=actor.id)
        self.chats.add_participant(chat.id, actor.id)
        self.chats.add_participant(chat.id, target.id)
        self.audit.log(admin_id=actor.id, action="create_direct_chat", entity_type="chat_room", entity_id=str(chat.id), payload={"target_admin_id": target.id})
        self.session.commit()
        return self.chats.get_chat(chat.id)

    def post_message(self, actor: Admin, chat_id: int, content: str):
        self.ensure_messages_enabled()
        content = content.strip()
        if not content:
            raise ValidationError("Сообщение не может быть пустым.")
        chat = self.get_chat_for_admin(actor, chat_id)
        message = self.chats.create_message(chat.id, actor.id, content)
        self.audit.log(admin_id=actor.id, action="post_chat_message", entity_type="chat_room", entity_id=str(chat.id), payload={"content": content[:120]})

        recipient_ids = []
        for participant in chat.participants:
            if participant.admin and participant.admin.is_active and participant.admin_id != actor.id:
                recipient_ids.append(participant.admin_id)

        sender_name = actor.full_name or actor.username
        for admin_id in recipient_ids:
            self.notifications.notify_admin(
                admin_id,
                kind="chat",
                title=f"Новое сообщение от {sender_name}",
                body=content[:180],
                link_url=f"/admin/chats-live/{chat.id}",
            )

        self.session.commit()
        return message

    def list_messages_after(self, actor: Admin, chat_id: int, after_id: int = 0):
        self.get_chat_for_admin(actor, chat_id)
        messages = self.chats.list_messages_after(chat_id, after_id=after_id)
        items = []
        for item in messages:
            items.append({
                "id": item.id,
                "admin_id": item.admin_id,
                "content": item.content,
                "created_at": item.created_at.isoformat(sep=" ", timespec="seconds") if item.created_at else "",
                "author_name": item.admin.full_name if item.admin and item.admin.full_name else (item.admin.username if item.admin else "Система"),
            })
        return items
