from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Category
from app.domain.dimensions import Dimension
from tests.test_scenarios_service import add_category, add_scenario

ROUND_LENGTH = get_settings().round_length


def log_in(client: TestClient, username: str = "player_one") -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "a long password",
        },
    )


def start_round(client: TestClient, **overrides: Any) -> Any:
    return client.post("/api/v1/rounds", json={"category_id": None, **overrides})


@pytest.fixture
def friendship(db: Session) -> Category:
    return add_category(db, "friendship")


def _fill_scenarios(db: Session, category: Category, count: int = ROUND_LENGTH) -> None:
    for i in range(count):
        add_scenario(db, category, f"f{i}")


def test_starting_a_round_requires_login(
    client_with_db: TestClient, db: Session, friendship: Category
) -> None:
    _fill_scenarios(db, friendship)

    response = start_round(client_with_db)

    assert response.status_code == 401


def test_not_enough_scenarios_returns_409(
    client_with_db: TestClient, db: Session, friendship: Category
) -> None:
    add_scenario(db, friendship, "only_one")
    log_in(client_with_db)

    response = start_round(client_with_db)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "not_enough_scenarios"


def test_full_playthrough_via_http(
    client_with_db: TestClient, db: Session, friendship: Category
) -> None:
    _fill_scenarios(db, friendship)
    log_in(client_with_db)

    state = start_round(client_with_db, category_id=friendship.id).json()
    assert state["status"] == "in_progress"
    assert state["current_question_number"] == 1
    round_id = state["id"]

    for _ in range(ROUND_LENGTH):
        question = state["question"]
        assert question is not None
        answer = client_with_db.post(
            f"/api/v1/rounds/{round_id}/answers",
            json={"scenario_id": question["id"], "choice_id": question["choices"][0]["id"]},
        )
        assert answer.status_code == 200
        state = answer.json()

    assert state["status"] == "completed"
    assert state["question"] is None
    assert state["result"]["scores"] == {"honesty": 1.0, "loyalty": 8.0}
    assert state["result"]["profile_key"] == "devoted-ally"

    fetched = client_with_db.get(f"/api/v1/rounds/{round_id}")
    assert fetched.status_code == 200
    assert fetched.json()["result"] == state["result"]


def test_answering_out_of_order_returns_409(
    client_with_db: TestClient, db: Session, friendship: Category
) -> None:
    _fill_scenarios(db, friendship)
    log_in(client_with_db)
    state = start_round(client_with_db, category_id=friendship.id).json()
    round_id = state["id"]
    current_scenario_id = state["question"]["id"]

    # Re-answering with the wrong scenario_id is rejected before it can advance the round.
    response = client_with_db.post(
        f"/api/v1/rounds/{round_id}/answers",
        json={
            "scenario_id": current_scenario_id + 1_000_000,
            "choice_id": state["question"]["choices"][0]["id"],
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "not_current_question"


def test_someone_elses_round_is_not_found(
    client_with_db: TestClient, db: Session, friendship: Category
) -> None:
    _fill_scenarios(db, friendship)
    log_in(client_with_db, "owner")
    round_id = start_round(client_with_db, category_id=friendship.id).json()["id"]
    client_with_db.post("/api/v1/auth/logout")
    log_in(client_with_db, "intruder")

    response = client_with_db.get(f"/api/v1/rounds/{round_id}")

    assert response.status_code == 404


def test_in_progress_response_never_contains_scoring_data(
    client_with_db: TestClient, db: Session, friendship: Category
) -> None:
    _fill_scenarios(db, friendship)
    log_in(client_with_db)

    text = start_round(client_with_db, category_id=friendship.id).text

    assert "weight" not in text.lower()
    for dimension in Dimension:
        assert f'"{dimension.value}"' not in text
