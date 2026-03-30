from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.core.database import SessionLocal
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.services.vk_bot_service import VKBotService

router = APIRouter(include_in_schema=False)
logger = get_logger(__name__)


@router.post('/api/vk/callback')
async def vk_callback(request: Request):
    payload = await request.json()
    with SessionLocal() as session:
        try:
            result = VKBotService(session).handle_callback(payload)
            session.commit()
            return PlainTextResponse(result)
        except ValidationError as exc:
            logger.warning('VK callback validation error: %s', exc)
            session.rollback()
            return PlainTextResponse('ok')
        except Exception as exc:
            logger.exception('VK callback failed', exc_info=exc)
            session.rollback()
            return PlainTextResponse('ok')
