from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.deps import get_db
from app.main import app


class _BrokenSession:
    def execute(self, *args: object, **kwargs: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))


def test_liveness_does_not_need_the_database(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": None}


def test_readiness_reports_503_when_database_is_down(client: TestClient) -> None:
    def broken_db() -> Iterator[_BrokenSession]:
        yield _BrokenSession()

    app.dependency_overrides[get_db] = broken_db

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "down"}


def test_readiness_ok_when_database_is_up(client_with_db: TestClient) -> None:
    response = client_with_db.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}
