from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command(commands=["help"]))
async def help_handler(message: Message) -> None:
    await message.answer(
        "Отправь цифровой код без лишних символов.\n"
        "Если хочешь написать в поддержку — просто отправь обычное сообщение."
    )
