from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AccountExistsError, InvalidCredentialsError
from app.core.security import dummy_password_hash, hash_password, verify_password
from app.db.models import User


def register_user(db: Session, *, username: str, email: str, password: str) -> User:
    """Create an account. `email` must already be normalized (lowercase)."""
    if _account_exists(db, username=username, email=email):
        raise AccountExistsError

    user = User(username=username, email=email, password_hash=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two people registering the same name at the same instant both pass the check
        # above; the unique indexes in the database are what really guarantee uniqueness.
        db.rollback()
        raise AccountExistsError from None
    return user


def authenticate(db: Session, *, email: str, password: str) -> User:
    """Return the user if the credentials are right, otherwise raise InvalidCredentialsError.

    Every failure looks identical to the caller, including its timing.
    """
    user = db.scalar(select(User).where(func.lower(User.email) == email))

    if user is None:
        # Hash something anyway so "unknown email" takes as long as "wrong password".
        verify_password(password, dummy_password_hash())
        raise InvalidCredentialsError

    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError
    return user


def _account_exists(db: Session, *, username: str, email: str) -> bool:
    found = db.scalar(
        select(User.id)
        .where(
            or_(
                func.lower(User.username) == username.lower(),
                func.lower(User.email) == email,
            )
        )
        .limit(1)
    )
    return found is not None
