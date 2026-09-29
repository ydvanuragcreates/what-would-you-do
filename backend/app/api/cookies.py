import uuid

from fastapi import Response

from app.core.config import get_settings
from app.core.security import create_access_token

COOKIE_NAME = "access_token"


def set_auth_cookie(response: Response, user_id: uuid.UUID) -> None:
    settings = get_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=create_access_token(user_id),
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,  # JavaScript can't read it, so an XSS bug can't steal the token
        secure=settings.cookie_secure,  # HTTPS only in production
        samesite="lax",  # not sent on cross-site POSTs, which blocks classic CSRF
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    # The browser hides httpOnly cookies from JavaScript, so only the server can delete it.
    response.delete_cookie(key=COOKIE_NAME, path="/")
