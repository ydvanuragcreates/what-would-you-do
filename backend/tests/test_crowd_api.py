"""The crowd statistics as a player experiences them over HTTP."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Scenario
from tests.crowd_helpers import make_player, record_round
from tests.test_results_api import ROUND_LENGTH, play_round
from tests.test_rounds_api import log_in, start_round
from tests.test_scenarios_service import add_category, add_scenario


@pytest.fixture
def scenarios(db: Session) -> list[Scenario]:
    category = add_category(db, "friendship")
    return [add_scenario(db, category, f"f{i}") for i in range(ROUND_LENGTH)]


@pytest.fixture
def small_crowd(db: Session, scenarios: list[Scenario], monkeypatch: pytest.MonkeyPatch) -> None:
    """Three other players have finished a round: two picked A everywhere, one picked B."""
    monkeypatch.setattr(get_settings(), "min_stats_sample", 3)
    for name, position in (("crowd_a1", 0), ("crowd_a2", 0), ("crowd_b", 1)):
        record_round(db, make_player(db, name), [(s, s.choices[position]) for s in scenarios])


def answer_first_question(client: TestClient, position: int = 2) -> tuple[dict, dict]:  # type: ignore[type-arg]
    """Start a round, answer question 1 with option `position`; return (question, response)."""
    state = start_round(client).json()
    question = state["question"]
    response = client.post(
        f"/api/v1/rounds/{state['id']}/answers",
        json={"scenario_id": question["id"], "choice_id": question["choices"][position]["id"]},
    )
    assert response.status_code == 200
    return question, response.json()


# --- the reveal right after answering ---------------------------------------------------------


@pytest.mark.usefixtures("small_crowd")
def test_answering_reveals_what_others_chose(client_with_db: TestClient) -> None:
    log_in(client_with_db)

    question, body = answer_first_question(client_with_db, position=2)

    reveal = body["last_answer"]
    assert reveal["scenario_id"] == question["id"]
    assert reveal["your_choice_id"] == question["choices"][2]["id"]
    crowd = reveal["crowd"]
    assert crowd["available"] is True
    assert crowd["total_responses"] == 3
    assert [(c["label"], c["percent"]) for c in crowd["choices"]] == [
        ("A", 67),
        ("B", 33),
        ("C", 0),
    ]
    assert crowd["message"] is None


@pytest.mark.usefixtures("small_crowd")
def test_reveal_leaks_nothing_about_who_answered(client_with_db: TestClient) -> None:
    log_in(client_with_db)

    _, body = answer_first_question(client_with_db)

    text = str(body).lower()
    for name in ("crowd_a1", "crowd_a2", "crowd_b", "example.com"):
        assert name not in text
    assert "weight" not in text


@pytest.mark.usefixtures("scenarios")
def test_too_few_responses_says_so_and_invents_nothing(client_with_db: TestClient) -> None:
    log_in(client_with_db)  # nobody else has played and the default minimum is 20

    _, body = answer_first_question(client_with_db)

    assert body["last_answer"]["crowd"] == {
        "available": False,
        "total_responses": None,
        "choices": [],
        "message": "Not enough responses yet.",
    }


@pytest.mark.usefixtures("small_crowd")
def test_the_reveal_only_appears_when_answering(client_with_db: TestClient) -> None:
    log_in(client_with_db)
    state = start_round(client_with_db).json()
    assert state["last_answer"] is None  # starting a round reveals nothing

    question = state["question"]
    client_with_db.post(
        f"/api/v1/rounds/{state['id']}/answers",
        json={"scenario_id": question["id"], "choice_id": question["choices"][0]["id"]},
    )

    refetched = client_with_db.get(f"/api/v1/rounds/{state['id']}").json()
    assert refetched["last_answer"] is None  # ...and it is not replayable from GET


@pytest.mark.usefixtures("small_crowd")
def test_your_own_answer_does_not_move_the_numbers(client_with_db: TestClient) -> None:
    log_in(client_with_db)
    state = start_round(client_with_db).json()
    question = state["question"]

    first = client_with_db.post(
        f"/api/v1/rounds/{state['id']}/answers",
        json={"scenario_id": question["id"], "choice_id": question["choices"][1]["id"]},
    ).json()

    assert first["last_answer"]["crowd"]["total_responses"] == 3  # you are not counted


# --- the final results page ---------------------------------------------------------------------


@pytest.mark.usefixtures("small_crowd")
def test_results_page_reviews_every_question(client_with_db: TestClient) -> None:
    log_in(client_with_db)
    round_id = play_round(client_with_db, position=2)

    body = client_with_db.get(f"/api/v1/results/{round_id}").json()

    questions = body["questions"]
    assert [q["question_number"] for q in questions] == list(range(1, ROUND_LENGTH + 1))
    assert len({q["scenario"]["id"] for q in questions}) == ROUND_LENGTH
    for question in questions:
        chosen = next(
            c for c in question["scenario"]["choices"] if c["id"] == question["your_choice_id"]
        )
        assert chosen["label"] == "C"  # we always picked the third option
        assert question["crowd"]["available"] is True
        assert sum(c["percent"] for c in question["crowd"]["choices"]) == 100
    assert "weight" not in str(body).lower()


@pytest.mark.usefixtures("scenarios")
def test_results_page_admits_when_there_is_not_enough_data(client_with_db: TestClient) -> None:
    log_in(client_with_db)
    round_id = play_round(client_with_db)

    questions = client_with_db.get(f"/api/v1/results/{round_id}").json()["questions"]

    assert all(q["crowd"]["available"] is False for q in questions)
    assert all(q["crowd"]["message"] == "Not enough responses yet." for q in questions)


@pytest.mark.usefixtures("small_crowd")
def test_reveal_and_results_page_agree(client_with_db: TestClient) -> None:
    """The number shown right after answering must match what the results page shows."""
    log_in(client_with_db)
    state = start_round(client_with_db).json()
    revealed: dict[int, list[int]] = {}
    for _ in range(ROUND_LENGTH):
        question = state["question"]
        state = client_with_db.post(
            f"/api/v1/rounds/{state['id']}/answers",
            json={"scenario_id": question["id"], "choice_id": question["choices"][1]["id"]},
        ).json()
        revealed[question["id"]] = [c["percent"] for c in state["last_answer"]["crowd"]["choices"]]

    questions = client_with_db.get(f"/api/v1/results/{state['id']}").json()["questions"]

    for question in questions:
        on_results_page = [c["percent"] for c in question["crowd"]["choices"]]
        assert on_results_page == revealed[question["scenario"]["id"]]
