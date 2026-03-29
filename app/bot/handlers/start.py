from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.main_menu import build_main_menu
from app.bot.state.session_state import clear_user_mode

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    clear_user_mode(message.from_user.id)
    await message.answer(
        "Привет. Выбери действие кнопкой ниже:\n"
        "• Поиск по коду — чтобы найти карточку\n"
        "• Репорт — чтобы написать в поддержку\n"
        "• Помощь — чтобы посмотреть инструкцию",
        reply_markup=build_main_menu(),
    )
