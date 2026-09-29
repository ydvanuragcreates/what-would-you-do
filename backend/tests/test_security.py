"""Password hashing and JWT logic. Pure functions: no database or HTTP needed."""

import base64
import json
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.errors import NotAuthenticatedError
from app.core.security import (
    JWT_ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

SECRET = "test-only-secret-never-use-outside-tests-0123456789"


def test_password_is_hashed_with_argon2_and_verifies() -> None:
    hashed = hash_password("correct horse battery")

    assert hashed.startswith("$argon2id$")
    assert "correct horse" not in hashed
    assert verify_password("correct horse battery", hashed)
    assert not verify_password("wrong password", hashed)


def test_same_password_gets_a_different_hash_each_time() -> None:
    # Random salt: two users with the same password must not have the same stored hash.
    assert hash_password("same password") != hash_password("same password")


def test_token_round_trip() -> None:
    user_id = uuid.uuid4()

    assert decode_access_token(create_access_token(user_id)) == user_id


def test_expired_token_is_rejected() -> None:
    long_ago = datetime.now(UTC) - timedelta(days=30)
    token = create_access_token(uuid.uuid4(), now=long_ago)

    with pytest.raises(NotAuthenticatedError):
        decode_access_token(token)


def test_token_signed_with_another_secret_is_rejected() -> None:
    forged = jwt.encode(
        {"sub": str(uuid.uuid4()), "exp": datetime.now(UTC) + timedelta(hours=1)},
        "some-other-secret-that-is-long-enough-1234567890",
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(NotAuthenticatedError):
        decode_access_token(forged)


def test_tampered_payload_is_rejected() -> None:
    """Swap in someone else's user id but keep the original signature."""
    victim, attacker = uuid.uuid4(), uuid.uuid4()
    header, _, signature = create_access_token(attacker).split(".")
    payload = json.loads(base64.urlsafe_b64decode(create_access_token(victim).split(".")[1] + "=="))
    fake_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()

    with pytest.raises(NotAuthenticatedError):
        decode_access_token(f"{header}.{fake_payload}.{signature}")


def test_unsigned_alg_none_token_is_rejected() -> None:
    unsigned = jwt.encode(
        {"sub": str(uuid.uuid4()), "exp": datetime.now(UTC) + timedelta(hours=1)},
        key=None,
        algorithm="none",
    )

    with pytest.raises(NotAuthenticatedError):
        decode_access_token(unsigned)


def test_token_without_expiry_is_rejected() -> None:
    no_expiry = jwt.encode({"sub": str(uuid.uuid4())}, SECRET, algorithm=JWT_ALGORITHM)

    with pytest.raises(NotAuthenticatedError):
        decode_access_token(no_expiry)


def test_token_with_non_uuid_subject_is_rejected() -> None:
    bad_subject = jwt.encode(
        {"sub": "not-a-uuid", "exp": datetime.now(UTC) + timedelta(hours=1)},
        SECRET,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(NotAuthenticatedError):
        decode_access_token(bad_subject)


@pytest.mark.parametrize("garbage", ["", "abc", "a.b.c", "Bearer xyz"])
def test_garbage_is_rejected(garbage: str) -> None:
    with pytest.raises(NotAuthenticatedError):
        decode_access_token(garbage)
