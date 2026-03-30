from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import Message

from app.bot.keyboards.main_menu import build_main_menu
from app.bot.state.session_state import USER_MODE_LOOKUP, clear_user_mode, get_user_mode
from app.bot.utils.formatter import build_lookup_caption, build_lookup_text
from app.core.database import SessionLocal
from app.repositories.media_asset_repository import MediaAssetRepository
from app.services.public_lookup_service import PublicLookupService
from app.services.telegram_media_service import TelegramMediaService

router = Router()
telegram_media_service = TelegramMediaService()


@router.message(F.text.regexp(r"^\d+$"))
async def code_lookup_handler(message: Message) -> None:
    code = (message.text or "").strip()
    mode = get_user_mode(message.from_user.id)
    if mode not in {None, USER_MODE_LOOKUP}:
        return

    clear_user_mode(message.from_user.id)
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    with SessionLocal() as session:
        try:
            result = PublicLookupService(session).lookup(code, source="telegram_bot")
        except Exception:
            await message.answer("Код не найден или неактивен.", reply_markup=build_main_menu())
            return

    caption = build_lookup_caption(result)
    text_fallback = build_lookup_text(result)

    try:
        media = await telegram_media_service.resolve(result)
        if media:
            if media.kind == "video":
                sent = await message.answer_video(video=media.payload, caption=caption, reply_markup=build_main_menu())
                _persist_telegram_file_id(result.asset_id, getattr(sent.video, "file_id", None))
                return
            if media.kind in {"image", "poster"}:
                sent = await message.answer_photo(photo=media.payload, caption=caption, reply_markup=build_main_menu())
                if sent.photo:
                    _persist_telegram_file_id(result.asset_id, sent.photo[-1].file_id)
                return

        await message.answer(text_fallback, disable_web_page_preview=True, reply_markup=build_main_menu())
    except Exception:
        await message.answer(text_fallback, disable_web_page_preview=True, reply_markup=build_main_menu())


def _persist_telegram_file_id(asset_id: int | None, file_id: str | None) -> None:
    if not asset_id or not file_id:
        return
    with SessionLocal() as session:
        repo = MediaAssetRepository(session)
        asset = repo.get_by_id(asset_id)
        if not asset:
            return
        if asset.telegram_file_id == file_id:
            return
        repo.update(asset, telegram_file_id=file_id)
        session.commit()
