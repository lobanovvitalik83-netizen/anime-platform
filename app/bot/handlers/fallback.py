from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards.main_menu import (
    MAIN_MENU_BUTTON_HELP,
    MAIN_MENU_BUTTON_LOOKUP,
    MAIN_MENU_BUTTON_REPORT,
    build_main_menu,
)
from app.bot.state.session_state import (
    USER_MODE_LOOKUP,
    USER_MODE_REPORT,
    clear_user_mode,
    set_user_mode,
)
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.site_setting_service import SiteSettingService

router = Router()


def _help_text() -> str:
    contact = settings.telegram_help_contact_text if getattr(settings, "telegram_help_contact_text", "").strip() else ""
    with SessionLocal() as session:
        db_contact = SiteSettingService(session).get_str("telegram_help_contact", "")
        if db_contact.strip():
            contact = db_contact.strip()
    if not contact:
        contact = "Контакт пока не указан"
    return (
        "Как пользоваться ботом:\n"
        "1. Нажми «Поиск по коду», потом отправь только цифры кода.\n"
        "2. Нажми «Репорт», если хочешь написать в поддержку.\n"
        "3. Ответ администратора придёт сюда же в этого бота.\n\n"
        f"Контакт: {contact}"
    )


@router.message(Command(commands=["help"]))
async def help_command_handler(message: Message) -> None:
    clear_user_mode(message.from_user.id)
    await message.answer(_help_text(), reply_markup=build_main_menu())


@router.message(F.text == MAIN_MENU_BUTTON_HELP)
async def help_button_handler(message: Message) -> None:
    clear_user_mode(message.from_user.id)
    await message.answer(_help_text(), reply_markup=build_main_menu())


@router.message(F.text == MAIN_MENU_BUTTON_LOOKUP)
async def lookup_button_handler(message: Message) -> None:
    set_user_mode(message.from_user.id, USER_MODE_LOOKUP)
    await message.answer(
        "Пришли только цифровой код без пробелов и лишних символов.",
        reply_markup=build_main_menu(),
    )


@router.message(F.text == MAIN_MENU_BUTTON_REPORT)
async def report_button_handler(message: Message) -> None:
    set_user_mode(message.from_user.id, USER_MODE_REPORT)
    await message.answer(
        "Опиши проблему обычным текстом. Можно отправить несколько сообщений подряд — они попадут в одно обращение.",
        reply_markup=build_main_menu(),
    )
