import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Category
from app.domain.dimensions import Dimension
from tests.test_rounds_api import log_in, start_round
from tests.test_scenarios_service import add_category, add_scenario

ROUND_LENGTH = get_settings().round_length


@pytest.fixture
def friendship(db: Session) -> Category:
    category = add_category(db, "friendship")
    for i in range(ROUND_LENGTH):
        add_scenario(db, category, f"f{i}")
    return category


def play_round(client: TestClient, *, category_id: int | None = None, position: int = 0) -> str:
    """Complete a whole round through the API, always picking option `position` (0=A, 1=B, 2=C)."""
    state = start_round(client, category_id=category_id).json()
    for _ in range(ROUND_LENGTH):
        question = state["question"]
        state = client.post(
            f"/api/v1/rounds/{state['id']}/answers",
            json={"scenario_id": question["id"], "choice_id": question["choices"][position]["id"]},
        ).json()
    assert state["status"] == "completed"
    return str(state["id"])


def result_of(client: TestClient, round_id: str) -> Any:
    return client.get(f"/api/v1/results/{round_id}")


# --- one result -----------------------------------------------------------------------------


def test_result_requires_login(client_with_db: TestClient) -> None:
    assert result_of(client_with_db, str(uuid.uuid4())).status_code == 401


def test_result_of_a_finished_round(client_with_db: TestClient, friendship: Category) -> None:
    log_in(client_with_db)
    round_id = play_round(client_with_db, category_id=friendship.id)

    response = result_of(client_with_db, round_id)

    assert response.status_code == 200
    body = response.json()
    assert body["round_id"] == round_id
    assert body["category_name"] == "Friendship"
    # always choosing option A gives honesty 1 and loyalty 8 (see add_scenario)
    assert body["profile"]["key"] == "devoted-ally"
    assert body["profile"]["title"] == "The Devoted Ally"
    assert "in this round" in body["profile"]["summary"]
    assert "not a psychological or moral assessment" in body["disclaimer"]


def test_result_lists_all_eight_dimensions_in_order(
    client_with_db: TestClient, friendship: Category
) -> None:
    log_in(client_with_db)
    round_id = play_round(client_with_db, category_id=friendship.id)

    scores = result_of(client_with_db, round_id).json()["scores"]

    assert [s["dimension"] for s in scores] == [d.value for d in Dimension]
    by_dimension = {s["dimension"]: s for s in scores}
    assert by_dimension["honesty"] == {"dimension": "honesty", "label": "Honesty", "score": 1.0}
    assert by_dimension["loyalty"]["score"] == 8.0
    assert by_dimension["self_interest"]["label"] == "Self-interest"
    # dimensions no scenario measured are reported as "not enough data", not as 0
    assert by_dimension["empathy"]["score"] is None


def test_random_round_is_labelled_random(client_with_db: TestClient, friendship: Category) -> None:
    log_in(client_with_db)
    round_id = play_round(client_with_db, category_id=None)

    assert result_of(client_with_db, round_id).json()["category_name"] == "Random"


def test_different_choices_give_a_different_profile(
    client_with_db: TestClient, friendship: Category
) -> None:
    log_in(client_with_db)
    # option C is honesty 3 / loyalty 6: nothing stands out, so "balanced"
    round_id = play_round(client_with_db, category_id=friendship.id, position=2)

    assert result_of(client_with_db, round_id).json()["profile"]["key"] == "balanced-decision-maker"


def test_result_is_not_available_while_the_round_is_in_progress(
    client_with_db: TestClient, friendship: Category
) -> None:
    log_in(client_with_db)
    round_id = start_round(client_with_db, category_id=friendship.id).json()["id"]

    response = result_of(client_with_db, round_id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "round_not_completed"


def test_unknown_round_is_404(client_with_db: TestClient) -> None:
    log_in(client_with_db)

    response = result_of(client_with_db, str(uuid.uuid4()))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "round_not_found"


def test_someone_elses_result_looks_exactly_like_a_missing_one(
    client_with_db: TestClient, friendship: Category
) -> None:
    log_in(client_with_db, "alice")
    alices_round = play_round(client_with_db, category_id=friendship.id)
    client_with_db.cookies.clear()
    log_in(client_with_db, "mallory")

    stolen = result_of(client_with_db, alices_round)
    missing = result_of(client_with_db, str(uuid.uuid4()))

    assert stolen.status_code == missing.status_code == 404
    assert stolen.json() == missing.json()  # can't tell "not yours" from "doesn't exist"


def test_result_response_never_contains_scoring_weights(
    client_with_db: TestClient, friendship: Category
) -> None:
    log_in(client_with_db)
    round_id = play_round(client_with_db, category_id=friendship.id)

    text = result_of(client_with_db, round_id).text.lower()

    assert "weight" not in text


# --- history --------------------------------------------------------------------------------


def test_history_requires_login(client_with_db: TestClient) -> None:
    assert client_with_db.get("/api/v1/users/me/results").status_code == 401


def test_history_starts_empty(client_with_db: TestClient) -> None:
    log_in(client_with_db)

    assert client_with_db.get("/api/v1/users/me/results").json() == {"total": 0, "results": []}


def test_history_lists_finished_rounds_newest_first(
    client_with_db: TestClient, friendship: Category
) -> None:
    log_in(client_with_db)
    first = play_round(client_with_db, category_id=friendship.id, position=0)
    second = play_round(client_with_db, category_id=None, position=2)

    body = client_with_db.get("/api/v1/users/me/results").json()

    assert body["total"] == 2
    assert [r["round_id"] for r in body["results"]] == [second, first]
    assert body["results"][0]["category_name"] == "Random"
    assert body["results"][0]["profile"]["key"] == "balanced-decision-maker"
    assert body["results"][1]["profile"]["key"] == "devoted-ally"


def test_history_skips_unfinished_rounds(client_with_db: TestClient, friendship: Category) -> None:
    log_in(client_with_db)
    finished = play_round(client_with_db, category_id=friendship.id)
    start_round(client_with_db, category_id=friendship.id)  # left in progress

    body = client_with_db.get("/api/v1/users/me/results").json()

    assert body["total"] == 1
    assert [r["round_id"] for r in body["results"]] == [finished]


def test_history_only_shows_your_own_rounds(
    client_with_db: TestClient, friendship: Category
) -> None:
    log_in(client_with_db, "alice")
    play_round(client_with_db, category_id=friendship.id)
    client_with_db.cookies.clear()
    log_in(client_with_db, "bob")

    assert client_with_db.get("/api/v1/users/me/results").json() == {"total": 0, "results": []}


def test_history_pagination(client_with_db: TestClient, friendship: Category) -> None:
    log_in(client_with_db)
    rounds = [play_round(client_with_db, category_id=friendship.id) for _ in range(3)]

    page = client_with_db.get("/api/v1/users/me/results", params={"limit": 2, "offset": 1}).json()

    assert page["total"] == 3  # the total ignores paging
    assert [r["round_id"] for r in page["results"]] == [rounds[1], rounds[0]]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 51}, {"offset": -1}])
def test_history_rejects_silly_paging(client_with_db: TestClient, params: dict[str, int]) -> None:
    log_in(client_with_db)

    assert client_with_db.get("/api/v1/users/me/results", params=params).status_code == 422
