from aiogram import F, Router
from aiogram.types import Message

from app.core.database import SessionLocal
from app.services.report_service import ReportService

router = Router()

@router.message(F.text)
async def report_support_handler(message: Message) -> None:
    text = (message.text or "").strip()
    if not text or text.startswith("/"):
        return
    full_name = " ".join([part for part in [message.from_user.first_name, message.from_user.last_name] if part]).strip() or None
    with SessionLocal() as session:
        try:
            ticket = ReportService(session).create_or_append_from_telegram(
                tg_user_id=message.from_user.id,
                tg_chat_id=message.chat.id,
                tg_username=message.from_user.username,
                tg_full_name=full_name,
                body=text,
            )
        except Exception:
            await message.answer("Не удалось отправить обращение. Попробуй позже.")
            return
    await message.answer(f"Обращение отправлено в поддержку. Номер: #{ticket.id}")
