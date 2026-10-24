from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    # Bcrypt strictly truncates passwords at 72 bytes; reject to prevent silent clipping
    if len(password_bytes) > 72:
        raise ValueError(
            "Password cannot be longer than 72 bytes"
        )
    return bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),  # Generates random salt with default work factor
    ).decode("utf-8")  # Convert bytes to string for database storage


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        return False
    return bcrypt.checkpw(
        password_bytes,
        password_hash.encode("utf-8"),
    )


def create_access_token(user_id: int) -> str:
    # Use timezone-aware UTC datetime for consistent token expiration
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload = {
        "sub": str(user_id),  # Standard JWT subject claim (must be string per RFC 7519)
        "exp": expire,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verify_access_token(
    token: str,
) -> int | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],  # Explicit whitelist prevents algorithm confusion attacks
        )
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    # Catches expired token, signature mismatch, or non-integer sub
    except (JWTError, ValueError, TypeError):
        return None