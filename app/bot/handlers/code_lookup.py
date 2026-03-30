from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import BufferedInputFile, Message

from app.bot.keyboards.main_menu import build_main_menu
from app.bot.state.session_state import USER_MODE_LOOKUP, clear_user_mode, get_user_mode
from app.bot.utils.formatter import build_lookup_caption, build_lookup_text
from app.core.database import SessionLocal
from app.services.media_delivery_service import MediaDeliveryService
from app.services.public_lookup_service import PublicLookupService

router = Router()

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
        if result.storage_kind == "telegram_file_id" and result.telegram_file_id:
            if result.asset_type == "video":
                await message.answer_video(video=result.telegram_file_id, caption=caption, reply_markup=build_main_menu())
                return
            if result.asset_type in {"image", "poster"}:
                await message.answer_photo(photo=result.telegram_file_id, caption=caption, reply_markup=build_main_menu())
                return

        delivered_media = MediaDeliveryService().fetch_lookup_media(result)
        if delivered_media:
            uploaded = BufferedInputFile(delivered_media.file_bytes, filename=delivered_media.file_name)
            if delivered_media.asset_type == "video":
                await message.answer_video(video=uploaded, caption=caption, reply_markup=build_main_menu())
                return
            if delivered_media.asset_type in {"image", "poster"}:
                await message.answer_photo(photo=uploaded, caption=caption, reply_markup=build_main_menu())
                return

        await message.answer(text_fallback, disable_web_page_preview=False, reply_markup=build_main_menu())
    except Exception:
        await message.answer(text_fallback, disable_web_page_preview=False, reply_markup=build_main_menu())
