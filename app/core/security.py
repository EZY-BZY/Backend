"""JWT and password hashing utilities."""

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings


def _password_for_bcrypt(password: str | bytes) -> str:
    """
    Map any UTF-8 password to a short fixed string for bcrypt.

    Bcrypt only accepts the first 72 bytes of its input. We SHA-256 the password and use the
    64-char hex digest (ASCII) so user passwords are not length-limited at the crypto layer.
    """
    if isinstance(password, bytes):
        pw = password
    else:
        pw = password.encode("utf-8")
    return hashlib.sha256(pw).hexdigest()


def verify_password(plain_password: str | bytes, hashed_password: str) -> bool:
    """Verify against a pre-hashed bcrypt password, or legacy bcrypt(raw) hashes."""
    stored = hashed_password.encode("utf-8")
    inner = _password_for_bcrypt(plain_password).encode("utf-8")
    try:
        if bcrypt.checkpw(inner, stored):
            return True
    except ValueError:
        pass
    # Legacy: bcrypt was applied to raw UTF-8 (only valid if password fits bcrypt's 72-byte limit)
    raw = (
        plain_password
        if isinstance(plain_password, bytes)
        else plain_password.encode("utf-8")
    )
    if len(raw) > 72:
        return False
    try:
        return bcrypt.checkpw(raw, stored)
    except ValueError:
        return False


def get_password_hash(password: str | bytes) -> str:
    """Hash a password (unlimited practical length via SHA-256 before bcrypt)."""
    settings = get_settings()
    inner = _password_for_bcrypt(password).encode("utf-8")
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    hashed = bcrypt.hashpw(inner, salt)
    return hashed.decode("ascii")


def create_access_token(
    subject: str | UUID,
    *,
    company_id: str | UUID | None = None,
    extra_claims: dict | None = None,
) -> str:
    """Create JWT access token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    if company_id is not None:
        payload["company_id"] = str(company_id)
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(subject: str | UUID) -> str:
    """Create JWT refresh token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str, expected_type: str | None = None) -> dict | None:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        if expected_type and payload.get("type") != expected_type:
            return None

        return payload

    except JWTError:
        return None
