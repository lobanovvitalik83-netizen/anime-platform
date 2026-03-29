import asyncio
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app.bot.handlers.code_lookup import router as code_lookup_router
from app.bot.handlers.fallback import router as fallback_router
from app.bot.handlers.report_support import router as report_support_router
from app.bot.handlers.start import router as start_router
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_dispatcher = None
_bot = None
_polling_task = None


def build_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(start_router)
    dispatcher.include_router(code_lookup_router)
    dispatcher.include_router(report_support_router)
    dispatcher.include_router(fallback_router)
    return dispatcher


async def start_bot_polling() -> None:
    global _dispatcher, _bot, _polling_task

    if not settings.telegram_bot_token:
        logger.info("Telegram bot token is not configured. Polling will not start.")
        return

    if _polling_task and not _polling_task.done():
        logger.info("Telegram bot polling already running.")
        return

    _dispatcher = build_dispatcher()
    _bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    async def _runner() -> None:
        logger.info("Telegram bot polling started")
        try:
            await _dispatcher.start_polling(_bot)
        finally:
            logger.info("Telegram bot polling stopped")

    _polling_task = asyncio.create_task(_runner())


async def stop_bot_polling() -> None:
    global _dispatcher, _bot, _polling_task

    if _dispatcher:
        with suppress(Exception):
            await _dispatcher.stop_polling()

    if _polling_task:
        with suppress(Exception):
            await _polling_task
        _polling_task = None

    if _bot:
        with suppress(Exception):
            await _bot.session.close()
        _bot = None

    _dispatcher = None
