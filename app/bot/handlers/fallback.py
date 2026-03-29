from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards.main_menu import MAIN_MENU_BUTTON_HELP, MAIN_MENU_BUTTON_LOOKUP, MAIN_MENU_BUTTON_REPORT, build_main_menu
from app.bot.state.session_state import USER_MODE_LOOKUP, USER_MODE_REPORT, clear_user_mode, get_user_mode, set_user_mode
from app.core.config import settings

router = Router()


def _help_text() -> str:
    return (
        "Как пользоваться ботом:\n"
        "1. Нажми «Поиск по коду» и отправь только цифры кода.\n"
        "2. Нажми «Репорт», если нужно написать в поддержку.\n"
        "3. Ответ из админки придёт сюда же в этого бота.\n\n"
        f"Контакт: {settings.telegram_help_contact_text}"
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
    await message.answer("Пришли только цифровой код без пробелов и лишних символов.", reply_markup=build_main_menu())


@router.message(F.text == MAIN_MENU_BUTTON_REPORT)
async def report_button_handler(message: Message) -> None:
    set_user_mode(message.from_user.id, USER_MODE_REPORT)
    await message.answer(
        "Опиши проблему одним или несколькими сообщениями.\nКогда захочешь выйти из режима репорта — нажми «Поиск по коду» или «Помощь».",
        reply_markup=build_main_menu(),
    )


@router.message(F.text)
async def fallback_text_handler(message: Message) -> None:
    text = (message.text or "").strip()
    mode = get_user_mode(message.from_user.id)
    if not text:
        return
    if mode == USER_MODE_LOOKUP and not text.isdigit():
        await message.answer("Для поиска нужен только цифровой код. Нажми «Репорт», если хочешь написать в поддержку.", reply_markup=build_main_menu())
        return
    if mode == USER_MODE_REPORT:
        return
    clear_user_mode(message.from_user.id)
    await message.answer("Выбери действие кнопкой ниже: поиск по коду, репорт или помощь.", reply_markup=build_main_menu())
