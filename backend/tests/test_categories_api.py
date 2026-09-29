from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Category
from app.domain.dimensions import Dimension
from tests.test_scenarios_service import add_scenario


def log_in(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"username": "player_one", "email": "p1@example.com", "password": "a long password"},
    )


def test_categories_require_login(client_with_db: TestClient) -> None:
    response = client_with_db.get("/api/v1/scenarios/categories")

    assert response.status_code == 401


def test_categories_listing(client_with_db: TestClient, db: Session) -> None:
    category = Category(slug="friendship", name="Friendship", emoji="F", sort_order=1)
    db.add(category)
    db.flush()
    add_scenario(db, category, "f1")
    log_in(client_with_db)

    response = client_with_db.get("/api/v1/scenarios/categories")

    assert response.status_code == 200
    body = response.json()
    assert body["round_length"] == 10
    assert body["random"] == {"scenario_count": 1, "playable": False}
    assert body["categories"] == [
        {
            "id": category.id,
            "slug": "friendship",
            "name": "Friendship",
            "emoji": "F",
            "scenario_count": 1,
            "playable": False,
        }
    ]


def test_categories_response_never_contains_scoring_data(
    client_with_db: TestClient, db: Session
) -> None:
    category = Category(slug="money", name="Money", sort_order=1)
    db.add(category)
    db.flush()
    add_scenario(db, category, "m1")
    log_in(client_with_db)

    text = client_with_db.get("/api/v1/scenarios/categories").text

    assert "weight" not in text.lower()
    for dimension in Dimension:
        assert f'"{dimension.value}"' not in text
