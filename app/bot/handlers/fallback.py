from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command(commands=["help"]))
async def help_handler(message: Message) -> None:
    await message.answer("Отправь цифровой код без лишних символов.")


@router.message(F.text)
async def fallback_handler(message: Message) -> None:
    await message.answer("Нужен цифровой код. Отправь только цифры.")
