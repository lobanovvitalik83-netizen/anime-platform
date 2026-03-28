import base64
import hashlib
import hmac
import json
import time
from typing import Any

from passlib.context import CryptContext

from app.core.config import settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7


def _normalize_password_for_bcrypt(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) <= 72:
        return password
    return hashlib.sha256(password_bytes).hexdigest()


def hash_password(password: str) -> str:
    normalized = _normalize_password_for_bcrypt(password)
    return password_context.hash(normalized)


def verify_password(plain_password: str, password_hash: str) -> bool:
    normalized = _normalize_password_for_bcrypt(plain_password)
    return password_context.verify(normalized, password_hash)


def _sign(payload: bytes) -> str:
    signature = hmac.new(
        settings.app_secret_key.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")


def create_session_token(admin_id: int) -> str:
    payload = {
        "admin_id": admin_id,
        "issued_at": int(time.time()),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_part = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    signature_part = _sign(raw)
    return f"{payload_part}.{signature_part}"


def verify_session_token(token: str) -> dict[str, Any] | None:
    try:
        payload_part, signature_part = token.split(".", 1)
        padded = payload_part + "=" * (-len(payload_part) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("utf-8"))

        expected_signature = _sign(raw)
        if not hmac.compare_digest(signature_part, expected_signature):
            return None

        payload = json.loads(raw.decode("utf-8"))
        issued_at = int(payload.get("issued_at", 0))
        if issued_at <= 0:
            return None

        if int(time.time()) - issued_at > SESSION_MAX_AGE_SECONDS:
            return None

        admin_id = int(payload.get("admin_id", 0))
        if admin_id <= 0:
            return None

        return {
            "admin_id": admin_id,
            "issued_at": issued_at,
        }
    except Exception:
        return None
