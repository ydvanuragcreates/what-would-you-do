import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.core.errors import NotAuthenticatedError

# Pinned, never read from the token or from config: accepting whatever algorithm
# the token claims is a classic JWT vulnerability ("alg": "none").
JWT_ALGORITHM = "HS256"

# argon2id with library-recommended parameters. The hash string records its own
# parameters and salt, so nothing else needs to be stored.
_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hash.verify(password, password_hash)


@lru_cache
def dummy_password_hash() -> str:
    """A valid hash of a throwaway value, used to spend the same time as a real check
    when the email doesn't exist, so response time doesn't reveal which emails are registered."""
    return _password_hash.hash("not-a-real-password")


def create_access_token(user_id: uuid.UUID, *, now: datetime | None = None) -> str:
    settings = get_settings()
    issued_at = now or datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    """Return the user id inside a valid token, or raise NotAuthenticatedError."""
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return uuid.UUID(claims["sub"])
    except (jwt.InvalidTokenError, ValueError):
        raise NotAuthenticatedError from None
