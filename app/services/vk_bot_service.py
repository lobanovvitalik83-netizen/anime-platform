import json
import secrets
from urllib import parse, request as urllib_request

from sqlalchemy.orm import Session

from app.bot.utils.formatter import build_lookup_plain_text
from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.core.security import report_rate_limiter
from app.services.media_delivery_service import MediaDeliveryService, MediaPayload
from app.services.public_lookup_service import PublicLookupService

logger = get_logger(__name__)

_USER_MODES: dict[int, str] = {}
USER_MODE_LOOKUP = 'lookup'
USER_MODE_REPORT = 'report'


class VKBotService:
    api_url = 'https://api.vk.com/method/messages.send'

    def __init__(self, session: Session | None = None):
        self.session = session

    def handle_callback(self, payload: dict) -> str:
        if not settings.vk_configured:
            raise ValidationError('VK bot is not configured.')
        if settings.vk_callback_secret:
            provided_secret = str(payload.get('secret', '')).strip()
            if provided_secret != settings.vk_callback_secret:
                raise ValidationError('Invalid VK callback secret.')
        callback_type = str(payload.get('type', '')).strip()
        if callback_type == 'confirmation':
            return settings.vk_callback_confirmation_token
        if callback_type == 'message_new':
            self._handle_message_new(payload)
            return 'ok'
        return 'ok'

    def _handle_message_new(self, payload: dict) -> None:
        if self.session is None:
            raise ValidationError('Session is required for VK message handling.')
        obj = payload.get('object') or {}
        message = obj.get('message') or obj
        text = str(message.get('text') or '').strip()
        from_id = int(message.get('from_id') or 0)
        peer_id = int(message.get('peer_id') or 0)
        if from_id <= 0 or peer_id == 0:
            return

        lower_text = text.lower()
        if lower_text in {'помощь', '/help', 'help', 'start', '/start'}:
            self._clear_mode(from_id)
            self.send_text(peer_id, self._help_text(), keyboard=self.build_main_keyboard())
            return
        if lower_text == 'поиск по коду':
            self._set_mode(from_id, USER_MODE_LOOKUP)
            self.send_text(peer_id, 'Пришли только цифровой код без пробелов и лишних символов.', keyboard=self.build_main_keyboard())
            return
        if lower_text == 'репорт':
            self._set_mode(from_id, USER_MODE_REPORT)
            self.send_text(peer_id, 'Опиши проблему одним или несколькими сообщениями. Для выхода нажми «Поиск по коду» или «Помощь».', keyboard=self.build_main_keyboard())
            return
        if not text:
            self.send_text(peer_id, self._welcome_text(), keyboard=self.build_main_keyboard())
            return

        current_mode = self._get_mode(from_id)
        if text.isdigit() and current_mode in {None, USER_MODE_LOOKUP}:
            self._clear_mode(from_id)
            self._handle_lookup(peer_id, text)
            return
        if current_mode == USER_MODE_REPORT:
            self._handle_report(from_id, peer_id, body=text)
            return
        self.send_text(peer_id, self._welcome_text(), keyboard=self.build_main_keyboard())

    def _handle_lookup(self, peer_id: int, code: str) -> None:
        if self.session is None:
            raise ValidationError('Session is required for VK lookup handling.')
        try:
            result = PublicLookupService(self.session).lookup(code, source='vk_bot')
        except Exception:
            self.send_text(peer_id, 'Код не найден или неактивен.', keyboard=self.build_main_keyboard())
            return

        text = build_lookup_plain_text(result)
        attachment = None
        if result.asset_type in {'image', 'poster'}:
            payload = MediaDeliveryService(self.session).resolve_media_payload(result)
            if payload is not None:
                try:
                    attachment = self._upload_message_photo(peer_id, payload)
                except Exception as exc:
                    logger.warning('VK photo upload failed for code=%s asset_id=%s: %s', code, result.asset_id, exc)

        self.send_text(peer_id, text, keyboard=self.build_main_keyboard(), attachment=attachment)

    def _handle_report(self, vk_user_id: int, peer_id: int, body: str) -> None:
        if self.session is None:
            raise ValidationError('Session is required for VK report handling.')
        from app.services.report_service import ReportService

        rate_key = f'vk-report:{vk_user_id}'
        allowed, retry_after = report_rate_limiter.is_allowed(
            rate_key,
            attempts=settings.report_rate_limit_attempts,
            window_seconds=settings.report_rate_limit_window_seconds,
        )
        if not allowed:
            self.send_text(peer_id, f'Слишком часто отправляешь репорты. Повтори через {retry_after} сек.', keyboard=self.build_main_keyboard())
            return
        try:
            ticket = ReportService(self.session).create_or_append_from_vk(
                vk_user_id=vk_user_id,
                vk_peer_id=peer_id,
                vk_full_name=f'VK user {vk_user_id}',
                body=body,
            )
        except Exception as exc:
            self.send_text(peer_id, f'Не удалось отправить обращение. Ошибка: {exc}', keyboard=self.build_main_keyboard())
            return
        self.send_text(peer_id, f'Обращение отправлено в поддержку. Номер обращения: #{ticket.id}', keyboard=self.build_main_keyboard())

    def send_text(
        self,
        peer_id: int,
        text: str,
        *,
        keyboard: dict | None = None,
        attachment: str | None = None,
    ) -> None:
        payload = {
            'peer_id': peer_id,
            'message': text,
            'random_id': secrets.randbelow(2_147_483_647),
        }
        if keyboard:
            payload['keyboard'] = json.dumps(keyboard, ensure_ascii=False)
        if attachment:
            payload['attachment'] = attachment
        self._call_api('messages.send', payload)

    def _upload_message_photo(self, peer_id: int, payload: MediaPayload) -> str:
        upload_server = self._call_api('photos.getMessagesUploadServer', {'peer_id': peer_id})
        upload_url = ((upload_server or {}).get('response') or {}).get('upload_url')
        if not upload_url:
            raise ValidationError('VK upload server did not return upload_url.')

        body, content_type = self._build_multipart_body(payload.file_bytes, payload.file_name, payload.mime_type)
        request = urllib_request.Request(
            upload_url,
            data=body,
            headers={'Content-Type': content_type},
            method='POST',
        )
        with urllib_request.urlopen(request, timeout=60) as response:
            upload_raw = response.read().decode('utf-8')
        upload_result = json.loads(upload_raw)

        saved = self._call_api(
            'photos.saveMessagesPhoto',
            {
                'photo': upload_result.get('photo', ''),
                'server': upload_result.get('server', ''),
                'hash': upload_result.get('hash', ''),
            },
        )
        items = (saved or {}).get('response') or []
        if not items:
            raise ValidationError('VK did not return saved photo metadata.')
        item = items[0]
        owner_id = item.get('owner_id')
        photo_id = item.get('id')
        if owner_id is None or photo_id is None:
            raise ValidationError('VK saved photo response is incomplete.')
        return f'photo{owner_id}_{photo_id}'

    def _call_api(self, method: str, payload: dict) -> dict:
        if not settings.vk_bot_token:
            raise ValidationError('VK_BOT_TOKEN не настроен.')
        request_payload = {
            **payload,
            'access_token': settings.vk_bot_token,
            'v': settings.vk_api_version,
        }
        data = parse.urlencode(request_payload).encode('utf-8')
        request = urllib_request.Request(f'https://api.vk.com/method/{method}', data=data)
        with urllib_request.urlopen(request, timeout=20) as response:
            raw = response.read().decode('utf-8')
        parsed = json.loads(raw)
        if 'error' in parsed:
            logger.error('VK %s failed: %s', method, parsed)
            raise ValidationError(f"VK API error: {parsed['error'].get('error_msg', 'unknown error')}")
        return parsed

    def _build_multipart_body(self, file_bytes: bytes, file_name: str, mime_type: str | None) -> tuple[bytes, str]:
        boundary = f'----MediaBridge{secrets.token_hex(16)}'
        safe_name = (file_name or 'image.jpg').replace('"', '')
        content_type = mime_type or 'image/jpeg'
        parts = [
            f'--{boundary}\r\n'.encode('utf-8'),
            f'Content-Disposition: form-data; name="photo"; filename="{safe_name}"\r\n'.encode('utf-8'),
            f'Content-Type: {content_type}\r\n\r\n'.encode('utf-8'),
            file_bytes,
            b'\r\n',
            f'--{boundary}--\r\n'.encode('utf-8'),
        ]
        body = b''.join(parts)
        return body, f'multipart/form-data; boundary={boundary}'

    def build_main_keyboard(self) -> dict:
        return {
            'one_time': False,
            'buttons': [
                [
                    {'action': {'type': 'text', 'label': 'Поиск по коду'}, 'color': 'primary'},
                    {'action': {'type': 'text', 'label': 'Репорт'}, 'color': 'negative'},
                ],
                [
                    {'action': {'type': 'text', 'label': 'Помощь'}, 'color': 'secondary'},
                ],
            ],
        }

    def _help_text(self) -> str:
        contact = settings.vk_help_contact_text.strip() or settings.telegram_help_contact_text.strip() or 'контакт пока не указан'
        return (
            'Как пользоваться VK-ботом:\n'
            '1. Нажми «Поиск по коду» и отправь только цифры кода.\n'
            '2. Нажми «Репорт», если нужно написать в поддержку.\n'
            '3. Ответ из админки придёт сюда же.\n\n'
            f'Контакт: {contact}'
        )

    def _welcome_text(self) -> str:
        return 'Выбери действие кнопкой ниже: поиск по коду, репорт или помощь.'

    def _set_mode(self, user_id: int, mode: str) -> None:
        _USER_MODES[user_id] = mode

    def _get_mode(self, user_id: int) -> str | None:
        return _USER_MODES.get(user_id)

    def _clear_mode(self, user_id: int) -> None:
        _USER_MODES.pop(user_id, None)
