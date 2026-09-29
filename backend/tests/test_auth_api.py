import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.cookies import COOKIE_NAME
from app.api.v1.auth import login_limiter
from app.core.security import create_access_token
from app.db.models import User

PASSWORD = "correct horse battery"


def register(client: TestClient, **overrides: Any) -> Any:
    payload = {"username": "anna_k", "email": "Anna@Example.com", "password": PASSWORD}
    return client.post("/api/v1/auth/register", json={**payload, **overrides})


def login(client: TestClient, email: str = "anna@example.com", password: str = PASSWORD) -> Any:
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


# --- registration -----------------------------------------------------------


def test_register_creates_account_and_logs_in(client_with_db: TestClient, db: Session) -> None:
    response = register(client_with_db)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "anna_k"
    assert body["email"] == "anna@example.com"  # normalized to lowercase
    assert "password" not in response.text.lower()

    # the password is stored only as an argon2 hash
    stored = db.scalars(select(User)).one()
    assert stored.password_hash != PASSWORD
    assert stored.password_hash.startswith("$argon2id$")

    # registering also logged us in: the cookie is set and works straight away
    assert client_with_db.get("/api/v1/auth/me").json()["id"] == body["id"]


def test_auth_cookie_is_httponly_and_samesite(client_with_db: TestClient) -> None:
    cookie = register(client_with_db).headers["set-cookie"].lower()

    assert cookie.startswith(f"{COOKIE_NAME}=")
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_duplicate_email_is_rejected_ignoring_case(client_with_db: TestClient) -> None:
    register(client_with_db)

    response = register(client_with_db, username="someone_else", email="ANNA@example.com")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "account_exists"


def test_duplicate_username_is_rejected_ignoring_case(client_with_db: TestClient) -> None:
    register(client_with_db)

    response = register(client_with_db, username="ANNA_K", email="other@example.com")

    assert response.status_code == 409


def test_duplicate_is_still_rejected_when_two_signups_race(
    client_with_db: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate the pre-check missing the other person's insert: the database must still refuse."""
    register(client_with_db)
    monkeypatch.setattr("app.services.auth._account_exists", lambda *a, **k: False)

    response = register(client_with_db)

    assert response.status_code == 409


@pytest.mark.parametrize(
    "overrides",
    [
        {"username": "ab"},  # too short
        {"username": "x" * 31},  # too long
        {"username": "has space"},
        {"username": "emoji😀"},
        {"email": "not-an-email"},
        {"password": "short"},  # under 8 characters
        {"password": "x" * 129},  # over the cap
    ],
)
def test_invalid_registration_is_rejected(
    client_with_db: TestClient, overrides: dict[str, str]
) -> None:
    response = register(client_with_db, **overrides)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_short_password_gets_a_readable_message(client_with_db: TestClient) -> None:
    response = register(client_with_db, password="short")

    assert response.json()["error"]["details"] == [
        {"field": "password", "message": "Password must be between 8 and 128 characters."}
    ]


def test_validation_errors_never_echo_the_password_back(client_with_db: TestClient) -> None:
    response = register(client_with_db, password="Zq9!x")

    assert response.status_code == 422
    assert "Zq9!x" not in response.text


def test_unknown_fields_are_rejected(client_with_db: TestClient) -> None:
    response = register(client_with_db, is_admin=True)

    assert response.status_code == 422


# --- login ------------------------------------------------------------------


def test_login_succeeds_and_sets_cookie(client_with_db: TestClient) -> None:
    register(client_with_db)
    client_with_db.cookies.clear()

    response = login(client_with_db)

    assert response.status_code == 200
    assert COOKIE_NAME in response.headers["set-cookie"]
    assert client_with_db.get("/api/v1/auth/me").status_code == 200


def test_login_email_is_case_insensitive(client_with_db: TestClient) -> None:
    register(client_with_db)

    assert login(client_with_db, email="  ANNA@EXAMPLE.COM ").status_code == 200


def test_wrong_password_and_unknown_email_look_identical(client_with_db: TestClient) -> None:
    register(client_with_db)

    wrong_password = login(client_with_db, password="not the password")
    unknown_email = login(client_with_db, email="nobody@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()  # can't discover which emails exist
    assert COOKIE_NAME not in wrong_password.headers.get("set-cookie", "")


# --- protected routes -------------------------------------------------------


def test_me_requires_login(client_with_db: TestClient) -> None:
    response = client_with_db.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_me_rejects_a_garbage_cookie(client_with_db: TestClient) -> None:
    client_with_db.cookies.set(COOKIE_NAME, "definitely.not.valid")

    assert client_with_db.get("/api/v1/auth/me").status_code == 401


def test_me_rejects_an_expired_token(client_with_db: TestClient, db: Session) -> None:
    user_id = register(client_with_db).json()["id"]
    long_ago = datetime.now(UTC) - timedelta(days=30)
    client_with_db.cookies.clear()
    client_with_db.cookies.set(COOKIE_NAME, create_access_token(uuid.UUID(user_id), now=long_ago))

    assert client_with_db.get("/api/v1/auth/me").status_code == 401


def test_me_rejects_a_valid_token_for_a_deleted_account(
    client_with_db: TestClient, db: Session
) -> None:
    client_with_db.cookies.set(COOKIE_NAME, create_access_token(uuid.uuid4()))

    assert client_with_db.get("/api/v1/auth/me").status_code == 401


def test_logout_clears_the_cookie(client_with_db: TestClient) -> None:
    register(client_with_db)
    assert client_with_db.get("/api/v1/auth/me").status_code == 200

    response = client_with_db.post("/api/v1/auth/logout")

    assert response.status_code == 204
    assert client_with_db.get("/api/v1/auth/me").status_code == 401


# --- rate limiting ----------------------------------------------------------


def test_login_is_rate_limited(client_with_db: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(login_limiter, "enabled", True)
    login_limiter.reset()
    try:
        for _ in range(login_limiter.max_requests):
            assert login(client_with_db, password="guess").status_code == 401

        blocked = login(client_with_db, password="guess")

        assert blocked.status_code == 429
        assert blocked.json()["error"]["code"] == "rate_limited"
        assert int(blocked.headers["retry-after"]) >= 1
    finally:
        login_limiter.reset()
