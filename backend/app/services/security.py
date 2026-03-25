from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password[:72], password_hash)

def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": subject, "type": token_type, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def create_access_token(subject: str) -> str:
    return create_token(subject, "access", timedelta(minutes=settings.jwt_access_token_expire_minutes))

def create_refresh_token(subject: str) -> str:
    return create_token(subject, "refresh", timedelta(days=settings.jwt_refresh_token_expire_days))

def decode_token(token: str, expected_type: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != expected_type:
            raise ValueError("Invalid token type")
        sub = payload.get("sub")
        if not sub:
            raise ValueError("Missing subject")
        return str(sub)
    except (JWTError, ValueError) as exc:
        raise ValueError("Could not validate credentials") from exc
