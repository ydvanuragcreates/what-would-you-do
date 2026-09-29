"""Shared test fixtures.

Database tests need a real PostgreSQL (our schema uses JSONB and functional indexes,
which SQLite can't do). Point TEST_DATABASE_URL at a *separate, disposable* database,
either as an environment variable or as a line in backend/.env:

    TEST_DATABASE_URL=postgresql://user:pass@host/wwyd_test

Without it, database tests are skipped and the rest of the suite still runs.
"""

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.main import app


def _test_database_url() -> str | None:
    # A real environment variable wins; otherwise fall back to the line in backend/.env.
    raw = os.environ.get("TEST_DATABASE_URL") or dotenv_values(".env").get("TEST_DATABASE_URL")
    if not raw:
        return None
    for prefix in ("postgres://", "postgresql://"):
        if raw.startswith(prefix):
            raw = "postgresql+psycopg://" + raw.removeprefix(prefix)
    # The suite drops and recreates every table. Refuse to touch anything that
    # isn't obviously a throwaway database.
    database = make_url(raw).database or ""
    if "test" not in database:
        pytest.exit(f"Refusing to run: TEST_DATABASE_URL database '{database}' must contain 'test'")
    return raw


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    url = _test_database_url()
    if url is None:
        pytest.skip("TEST_DATABASE_URL not set; skipping database tests")

    # Build the schema through the real migrations, so the migrations are tested too.
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")

    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """A session whose work is rolled back after each test, leaving the DB clean."""
    with engine.connect() as connection:
        outer = connection.begin()
        session = Session(
            bind=connection, join_transaction_mode="create_savepoint", autoflush=False
        )
        try:
            yield session
        finally:
            session.close()
            outer.rollback()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_db(client: TestClient, db: Session) -> TestClient:
    """A client whose requests use the test session instead of the real database."""
    app.dependency_overrides[get_db] = lambda: db
    return client
