from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.admin import Admin
from app.repositories.report_repository import ReportRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.site_setting_service import SiteSettingService


class ReportService:
    def __init__(self, session: Session):
        self.session = session
        self.reports = ReportRepository(session)
        self.audit = AuditService(session)
        self.settings = SiteSettingService(session)
        self.notifications = NotificationService(session)

    def ensure_reports_enabled(self):
        if not self.settings.is_reports_enabled():
            raise ValidationError("Репорты временно отключены.")

    def list_tickets(self):
        return self.reports.list_tickets()

    def get_ticket(self, ticket_id: int):
        ticket = self.reports.get_ticket(ticket_id)
        if not ticket:
            raise NotFoundError("Репорт не найден.")
        return ticket

    def create_or_append_from_telegram(
        self,
        *,
        tg_user_id: int,
        tg_chat_id: int,
        tg_username: str | None,
        tg_full_name: str | None,
        body: str,
    ):
        self.ensure_reports_enabled()
        body = body.strip()
        if not body:
            raise ValidationError("Пустой репорт не создаётся.")

        ticket = self.reports.get_open_ticket_by_tg_user_id(tg_user_id)
        is_new = False
        if not ticket:
            topic = f"Support: @{tg_username}" if tg_username else f"Support #{tg_user_id}"
            ticket = self.reports.create_ticket(
                tg_user_id=tg_user_id,
                tg_chat_id=tg_chat_id,
                tg_username=tg_username,
                tg_full_name=tg_full_name,
                status="open",
                topic=topic,
                last_message_preview=body[:200],
                assigned_admin_id=None,
            )
            self.audit.log(None, "create_report_ticket", "report_ticket", str(ticket.id), {"tg_user_id": tg_user_id})
            is_new = True
        else:
            ticket = self.reports.update_ticket(ticket, status="open", last_message_preview=body[:200])

        self.reports.create_message(
            ticket_id=ticket.id,
            direction="user",
            admin_id=None,
            tg_user_id=tg_user_id,
            body=body,
        )

        title = f"Новый репорт #{ticket.id}" if is_new else f"Новое сообщение в репорте #{ticket.id}"
        author = tg_full_name or (f"@{tg_username}" if tg_username else str(tg_user_id))
        self.notifications.notify_by_permission(
            "reports_view",
            kind="report",
            title=title,
            body=f"От {author}: {body[:180]}",
            link_url=f"/admin/reports/{ticket.id}",
        )

        self.session.commit()
        return ticket

    async def reply_from_admin(self, actor: Admin, ticket_id: int, body: str):
        self.ensure_reports_enabled()
        body = body.strip()
        if not body:
            raise ValidationError("Сообщение пустое.")
        ticket = self.get_ticket(ticket_id)
        ticket = self.reports.update_ticket(
            ticket,
            status="in_progress",
            assigned_admin_id=actor.id,
            last_message_preview=body[:200],
        )
        self.reports.create_message(
            ticket_id=ticket.id,
            direction="admin",
            admin_id=actor.id,
            tg_user_id=ticket.tg_user_id,
            body=body,
        )
        await self._send_to_telegram(ticket.tg_chat_id, body)
        self.audit.log(actor.id, "reply_report_ticket", "report_ticket", str(ticket.id), {"tg_user_id": ticket.tg_user_id})
        self.session.commit()
        return self.get_ticket(ticket.id)

    def close_ticket(self, actor: Admin, ticket_id: int):
        ticket = self.get_ticket(ticket_id)
        self.reports.update_ticket(ticket, status="closed", assigned_admin_id=actor.id)
        self.audit.log(actor.id, "close_report_ticket", "report_ticket", str(ticket.id), {"tg_user_id": ticket.tg_user_id})
        self.session.commit()
        return ticket

    async def _send_to_telegram(self, chat_id: int, body: str):
        if not settings.telegram_bot_token:
            raise ValidationError("TELEGRAM_BOT_TOKEN не настроен.")
        bot = Bot(token=settings.telegram_bot_token, default=DefaultBotProperties(parse_mode="HTML"))
        try:
            await bot.send_message(chat_id=chat_id, text=body)
        finally:
            await bot.session.close()
