from collections.abc import Iterator
from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.api.cookies import COOKIE_NAME
from app.core.errors import NotAuthenticatedError
from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import SessionLocal


def get_db() -> Iterator[Session]:
    """One database session per request, always closed afterwards.

    Convention: services call `db.commit()` themselves when a use case succeeds.
    Route handlers never commit.
    """
    with SessionLocal() as db:
        yield db


DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> User:
    """Who is making this request? Add `user: CurrentUser` to any endpoint to protect it.

    The user id comes ONLY from the signed token, never from the URL or request body.
    """
    if token is None:
        raise NotAuthenticatedError
    user = db.get(User, decode_access_token(token))
    if user is None:  # valid signature, but the account no longer exists
        raise NotAuthenticatedError
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
