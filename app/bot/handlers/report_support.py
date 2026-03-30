from aiogram import F, Router
from aiogram.types import Message

from app.bot.keyboards.main_menu import (
    MAIN_MENU_BUTTON_HELP,
    MAIN_MENU_BUTTON_LOOKUP,
    MAIN_MENU_BUTTON_REPORT,
    build_main_menu,
)
from app.bot.state.session_state import USER_MODE_REPORT, get_user_mode
from app.core.database import SessionLocal
from app.services.report_service import ReportService

router = Router()


@router.message(
    F.text,
    ~F.text.startswith("/"),
    ~F.text.in_({MAIN_MENU_BUTTON_HELP, MAIN_MENU_BUTTON_LOOKUP, MAIN_MENU_BUTTON_REPORT}),
)
async def report_support_handler(message: Message) -> None:
    text = (message.text or "").strip()
    if not text:
        return
    if text.isdigit():
        return
    if get_user_mode(message.from_user.id) != USER_MODE_REPORT:
        return

    full_name = " ".join(
        [part for part in [message.from_user.first_name, message.from_user.last_name] if part]
    ).strip() or None

    with SessionLocal() as session:
        try:
            ticket = ReportService(session).create_or_append_from_telegram(
                tg_user_id=message.from_user.id,
                tg_chat_id=message.chat.id,
                tg_username=message.from_user.username,
                tg_full_name=full_name,
                body=text,
            )
        except Exception as exc:
            await message.answer(
                f"Не удалось отправить обращение. Ошибка: {exc}",
                reply_markup=build_main_menu(),
            )
            return

    await message.answer(
        f"Обращение отправлено в поддержку. Номер обращения: #{ticket.id}",
        reply_markup=build_main_menu(),
    )
