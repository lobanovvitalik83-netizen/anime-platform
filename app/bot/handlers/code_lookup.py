from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import BufferedInputFile, Message

from app.bot.keyboards.main_menu import build_main_menu
from app.bot.state.session_state import USER_MODE_LOOKUP, clear_user_mode, get_user_mode
from app.bot.utils.formatter import build_lookup_caption, build_lookup_text
from app.core.database import SessionLocal
from app.models.media_asset import MediaAsset
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
            if result.asset_type == "video":
                if result.storage_kind == "telegram_file_id" and result.telegram_file_id:
                    await message.answer_video(video=result.telegram_file_id, caption=caption, reply_markup=build_main_menu())
                    return
                if result.external_url:
                    await message.answer_video(video=result.external_url, caption=caption, reply_markup=build_main_menu())
                    return

            if result.asset_type in {"image", "poster"}:
                if result.storage_kind == "telegram_file_id" and result.telegram_file_id:
                    await message.answer_photo(photo=result.telegram_file_id, caption=caption, reply_markup=build_main_menu())
                    return

                payload = MediaDeliveryService().resolve_media_payload(
                    asset_id=result.asset_id,
                    external_url=result.external_url,
                    asset_type=result.asset_type,
                    mime_type=result.mime_type,
                )
                if payload:
                    sent = await message.answer_photo(
                        photo=BufferedInputFile(payload.content, filename=payload.filename),
                        caption=caption,
                        reply_markup=build_main_menu(),
                    )
                    if result.asset_id and sent.photo:
                        asset = session.get(MediaAsset, result.asset_id)
                        if asset:
                            asset.telegram_file_id = sent.photo[-1].file_id
                            asset.storage_kind = "telegram_file_id"
                            session.commit()
                    return

            await message.answer(text_fallback, disable_web_page_preview=True, reply_markup=build_main_menu())
        except Exception:
            await message.answer(text_fallback, disable_web_page_preview=True, reply_markup=build_main_menu())
