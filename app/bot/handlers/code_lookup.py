from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import Message

from app.bot.keyboards.main_menu import build_main_menu
from app.bot.state.session_state import USER_MODE_LOOKUP, clear_user_mode, get_user_mode
from app.bot.utils.formatter import build_lookup_caption, build_lookup_text
from app.core.database import SessionLocal
from app.services.media_delivery_service import MediaDeliveryService
from app.services.public_lookup_service import PublicLookupService

router = Router()


@router.message(F.text.regexp(r"^\d+$"))
async def code_lookup_handler(message: Message) -> None:
    code = (message.text or '').strip()
    mode = get_user_mode(message.from_user.id)
    if mode not in {None, USER_MODE_LOOKUP}:
        return

    clear_user_mode(message.from_user.id)
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    with SessionLocal() as session:
        try:
            result = PublicLookupService(session).lookup(code, source='telegram_bot')
        except Exception:
            await message.answer('Код не найден или неактивен.', reply_markup=build_main_menu())
            return

        caption = build_lookup_caption(result)
        text_fallback = build_lookup_text(result)
        media_delivery = MediaDeliveryService(session)

        try:
            if result.asset_type == 'video':
                if result.telegram_file_id:
                    await message.answer_video(video=result.telegram_file_id, caption=caption, reply_markup=build_main_menu())
                    return
                if result.external_url:
                    await message.answer_video(video=result.external_url, caption=caption, reply_markup=build_main_menu())
                    return

            if result.asset_type in {'image', 'poster'}:
                if result.telegram_file_id:
                    await message.answer_photo(photo=result.telegram_file_id, caption=caption, reply_markup=build_main_menu())
                    return

                resolved = await media_delivery.resolve_for_telegram(result)
                if resolved is not None:
                    sent = await message.answer_photo(
                        photo=media_delivery.build_telegram_input_file(resolved),
                        caption=caption,
                        reply_markup=build_main_menu(),
                    )
                    telegram_file_id = None
                    if getattr(sent, 'photo', None):
                        telegram_file_id = sent.photo[-1].file_id
                    if telegram_file_id:
                        media_delivery.persist_telegram_file_id(result.asset_id, telegram_file_id)
                    return

            await message.answer(text_fallback, disable_web_page_preview=True, reply_markup=build_main_menu())
        except Exception:
            await message.answer(text_fallback, disable_web_page_preview=True, reply_markup=build_main_menu())
