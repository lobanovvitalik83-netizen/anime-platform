from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import BufferedInputFile, Message

from app.bot.keyboards.main_menu import build_main_menu
from app.bot.state.session_state import USER_MODE_LOOKUP, clear_user_mode, get_user_mode
from app.bot.utils.formatter import build_lookup_caption, build_lookup_text
from app.core.database import SessionLocal
from app.repositories.media_asset_repository import MediaAssetRepository
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
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO)

    with SessionLocal() as session:
        try:
            result = PublicLookupService(session).lookup(code, source="telegram_bot")
        except Exception:
            await message.answer("Код не найден или неактивен.", reply_markup=build_main_menu())
            return

    caption = build_lookup_caption(result)
    text_fallback = build_lookup_text(result)

    try:
        if result.asset_type in {"image", "poster"}:
            if result.telegram_file_id:
                await message.answer_photo(photo=result.telegram_file_id, caption=caption, reply_markup=build_main_menu())
                return

            payload = MediaDeliveryService().resolve_payload(result)
            if payload:
                sent = await message.answer_photo(
                    photo=BufferedInputFile(payload.data, filename=payload.filename),
                    caption=caption,
                    reply_markup=build_main_menu(),
                )
                file_id = None
                if sent.photo:
                    file_id = sent.photo[-1].file_id
                if file_id and result.asset_id:
                    with SessionLocal() as session:
                        asset = MediaAssetRepository(session).get_by_id(result.asset_id)
                        if asset and asset.telegram_file_id != file_id:
                            MediaAssetRepository(session).update(asset, telegram_file_id=file_id)
                            session.commit()
                return

        await message.answer(text_fallback, disable_web_page_preview=True, reply_markup=build_main_menu())
    except Exception:
        await message.answer(text_fallback, disable_web_page_preview=True, reply_markup=build_main_menu())
