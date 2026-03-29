import base64
import hashlib
import hmac
import json
import secrets
import string
import time
from typing import Any

from app.core.config import settings

SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
PBKDF2_ITERATIONS = 390000
PASSWORD_SCHEME = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    salt_b64 = base64.urlsafe_b64encode(salt).decode("utf-8").rstrip("=")
    hash_b64 = base64.urlsafe_b64encode(derived_key).decode("utf-8").rstrip("=")
    return f"{PASSWORD_SCHEME}${PBKDF2_ITERATIONS}${salt_b64}${hash_b64}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        scheme, iterations_str, salt_b64, hash_b64 = password_hash.split("$", 3)
        if scheme != PASSWORD_SCHEME:
            return False

        iterations = int(iterations_str)
        salt = _urlsafe_b64decode(salt_b64)
        expected_hash = _urlsafe_b64decode(hash_b64)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False


def generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(length))
        if any(ch.islower() for ch in value) and any(ch.isupper() for ch in value) and any(ch.isdigit() for ch in value):
            return value


def _urlsafe_b64decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


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
        raw = _urlsafe_b64decode(payload_part)

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
