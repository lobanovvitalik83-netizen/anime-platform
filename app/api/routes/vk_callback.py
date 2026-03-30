import json
import secrets
import time
from collections import deque
from html import unescape
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Request as FastAPIRequest

from app.bot.state.session_state import USER_MODE_LOOKUP, USER_MODE_REPORT, clear_user_mode, get_user_mode, set_user_mode
from app.bot.utils.formatter import build_lookup_plain_text
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.public_lookup_service import PublicLookupService
from app.services.report_service import ReportService

router = APIRouter(include_in_schema=False)

_recent_event_ids: deque[tuple[str, float]] = deque(maxlen=1000)
_recent_seen: set[str] = set()


def _is_duplicate_event(event_id: str | None) -> bool:
    if not event_id:
        return False
    now = time.time()
    while _recent_event_ids and _recent_event_ids[0][1] < now - 900:
        old_id, _ = _recent_event_ids.popleft()
        _recent_seen.discard(old_id)
    if event_id in _recent_seen:
        return True
    _recent_event_ids.append((event_id, now))
    _recent_seen.add(event_id)
    return False


def _vk_api(method: str, payload: dict) -> dict:
    if not settings.vk_bot_token:
        return {}
    body = urlencode({**payload, "access_token": settings.vk_bot_token, "v": settings.vk_api_version}).encode("utf-8")
    request = Request(
        url=f"https://api.vk.com/method/{method}",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def _send_message(peer_id: int, text: str, attachment: str | None = None, keyboard: dict | None = None) -> None:
    payload = {
        "peer_id": peer_id,
        "random_id": int(time.time() * 1000000) ^ secrets.randbelow(1000000),
        "message": text,
    }
    if attachment:
        payload["attachment"] = attachment
    if keyboard:
        payload["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    _vk_api("messages.send", payload)


def _build_main_keyboard() -> dict:
    return {
        "one_time": False,
        "inline": False,
        "buttons": [
            [
                {"action": {"type": "text", "label": "Поиск по коду"}, "color": "primary"},
                {"action": {"type": "text", "label": "Репорт"}, "color": "negative"},
            ],
            [
                {"action": {"type": "text", "label": "Помощь"}, "color": "secondary"},
            ],
        ],
    }


def _send_menu(peer_id: int, text: str, attachment: str | None = None) -> None:
    _send_message(peer_id, text, attachment=attachment, keyboard=_build_main_keyboard())


def _upload_external_photo_for_message(peer_id: int, photo_url: str) -> str | None:
    try:
        upload_info = _vk_api("photos.getMessagesUploadServer", {"peer_id": peer_id})
        upload_url = ((upload_info or {}).get("response") or {}).get("upload_url")
        if not upload_url:
            return None

        with urlopen(photo_url, timeout=30) as src:
            photo_bytes = src.read()
            content_type = src.headers.get_content_type() or "image/jpeg"

        boundary = "----WebKitFormBoundary" + secrets.token_hex(12)
        crlf = "\r\n"
        body = b""
        body += f"--{boundary}{crlf}".encode()
        body += f'Content-Disposition: form-data; name="photo"; filename="image.jpg"{crlf}'.encode()
        body += f"Content-Type: {content_type}{crlf}{crlf}".encode()
        body += photo_bytes + crlf.encode()
        body += f"--{boundary}--{crlf}".encode()

        req = Request(
            upload_url,
            data=body,
            method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        with urlopen(req, timeout=60) as uploaded:
            upload_result = json.loads(uploaded.read().decode("utf-8") or "{}")

        saved = _vk_api(
            "photos.saveMessagesPhoto",
            {
                "photo": upload_result.get("photo", ""),
                "server": upload_result.get("server", ""),
                "hash": upload_result.get("hash", ""),
            },
        )
        saved_items = (saved or {}).get("response") or []
        if not saved_items:
            return None
        item = saved_items[0]
        access_key = item.get("access_key")
        if access_key:
            return f"photo{item['owner_id']}_{item['id']}_{access_key}"
        return f"photo{item['owner_id']}_{item['id']}"
    except Exception:
        return None


@router.post("/api/vk/callback")
async def vk_callback(request: FastAPIRequest):
    payload = await request.json()

    if settings.vk_callback_secret.strip():
        if str(payload.get("secret", "")).strip() != settings.vk_callback_secret.strip():
            raise HTTPException(status_code=403, detail="Invalid callback secret")

    event_type = str(payload.get("type", "")).strip()

    if event_type == "confirmation":
        return settings.vk_callback_confirmation_token.strip()

    if event_type != "message_new":
        return "ok"

    if _is_duplicate_event(str(payload.get("event_id", "")).strip()):
        return "ok"

    message = (payload.get("object") or {}).get("message") or {}
    text = str(message.get("text", "")).strip()
    peer_id = int(message.get("peer_id") or 0)
    from_id = int(message.get("from_id") or 0)
    if not peer_id or not from_id:
        return "ok"

    normalized = text.lower()

    if normalized in {"/start", "старт", "start"}:
        clear_user_mode(from_id)
        _send_menu(peer_id, "Привет. Выбери действие кнопкой ниже.")
        return "ok"

    if normalized == "поиск по коду":
        set_user_mode(from_id, USER_MODE_LOOKUP)
        _send_menu(peer_id, "Пришли только цифровой код.")
        return "ok"

    if normalized == "репорт":
        set_user_mode(from_id, USER_MODE_REPORT)
        _send_menu(peer_id, "Опиши проблему одним сообщением.")
        return "ok"

    if normalized == "помощь":
        clear_user_mode(from_id)
        help_contact = settings.vk_help_contact.strip() or settings.telegram_help_contact_text.strip() or "Контакт пока не указан."
        _send_menu(peer_id, f"Помощь:\n• Поиск по коду\n• Репорт\n• Контакт: {help_contact}")
        return "ok"

    if text.isdigit() and get_user_mode(from_id) in {None, USER_MODE_LOOKUP}:
        clear_user_mode(from_id)
        with SessionLocal() as session:
            try:
                result = PublicLookupService(session).lookup(text, source="vk_bot")
                msg = build_lookup_plain_text(result)
                attachment = None
                if result.asset_type in {"image", "poster"} and result.external_url:
                    attachment = _upload_external_photo_for_message(peer_id, result.external_url)
                _send_menu(peer_id, msg, attachment=attachment)
            except Exception:
                _send_menu(peer_id, "Код не найден или неактивен.")
        return "ok"

    if get_user_mode(from_id) == USER_MODE_REPORT and text:
        clear_user_mode(from_id)
        with SessionLocal() as session:
            try:
                ReportService(session).create_or_append_from_telegram(
                    tg_user_id=from_id,
                    tg_chat_id=peer_id,
                    tg_username=None,
                    tg_full_name="VK user",
                    body=f"[VK] {text}",
                )
                _send_menu(peer_id, "Обращение отправлено в поддержку.")
            except Exception as exc:
                _send_menu(peer_id, f"Не удалось отправить обращение. Ошибка: {exc}")
        return "ok"

    _send_menu(peer_id, "Выбери действие кнопкой ниже.")
    return "ok"
