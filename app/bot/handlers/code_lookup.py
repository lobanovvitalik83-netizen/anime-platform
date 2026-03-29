from aiogram import F, Router
from aiogram.types import Message

from app.bot.utils.formatter import build_lookup_caption
from app.core.database import SessionLocal
from app.services.public_lookup_service import PublicLookupService

router = Router()


@router.message(F.text.regexp(r"^\d+$"))
async def code_lookup_handler(message: Message) -> None:
    code = (message.text or "").strip()

    with SessionLocal() as session:
        try:
            result = PublicLookupService(session).lookup(code)
        except Exception:
            await message.answer("Код не найден или неактивен.")
            return

    caption = build_lookup_caption(result)

    try:
        if result.storage_kind == "telegram_file_id" and result.telegram_file_id:
            if result.asset_type == "video":
                await message.answer_video(video=result.telegram_file_id, caption=caption)
                return
            if result.asset_type in {"image", "poster"}:
                await message.answer_photo(photo=result.telegram_file_id, caption=caption)
                return

        if result.storage_kind == "external_url" and result.external_url:
            if result.asset_type == "video":
                await message.answer_video(video=result.external_url, caption=caption)
                return
            if result.asset_type in {"image", "poster"}:
                await message.answer_photo(photo=result.external_url, caption=caption)
                return

        text = caption
        if result.external_url:
            text += f"\n\nСсылка: {result.external_url}"
        await message.answer(text, disable_web_page_preview=False)

    except Exception:
        text = caption
        if result.external_url:
            text += f"\n\nСсылка: {result.external_url}"
        await message.answer(text, disable_web_page_preview=False)
