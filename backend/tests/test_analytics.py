import random
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.db.models import Scenario, User
from app.db.models.enums import RoundStatus
from app.schemas.crowd import ChoiceShare, CrowdStats
from app.services.analytics import (
    NOT_ENOUGH_RESPONSES,
    crowd_stats_for,
    largest_remainder_percentages,
)
from tests.crowd_helpers import make_player, record_round
from tests.test_scenarios_service import add_category, add_scenario

T0 = datetime(2026, 1, 1, tzinfo=UTC)


# --- the percentage maths (no database) ---------------------------------------------------


def test_percentages_match_the_plan_example() -> None:
    assert largest_remainder_percentages({1: 24, 2: 51, 3: 25}) == {1: 24, 2: 51, 3: 25}


def test_thirds_add_up_to_exactly_100() -> None:
    """Plain rounding gives 33 + 33 + 33 = 99."""
    result = largest_remainder_percentages({1: 1, 2: 1, 3: 1})

    assert sum(result.values()) == 100
    assert sorted(result.values()) == [33, 33, 34]


def test_leftover_points_go_to_the_biggest_lost_fractions() -> None:
    # exact: 44.44 / 33.33 / 22.22 -> floors 44/33/22 (sum 99) -> the extra point goes to id 1
    assert largest_remainder_percentages({1: 4, 2: 3, 3: 2}) == {1: 45, 2: 33, 3: 22}


def test_no_answers_gives_zeros() -> None:
    assert largest_remainder_percentages({1: 0, 2: 0, 3: 0}) == {1: 0, 2: 0, 3: 0}


def test_everyone_picked_the_same_option() -> None:
    assert largest_remainder_percentages({1: 7, 2: 0, 3: 0}) == {1: 100, 2: 0, 3: 0}


def test_percentages_always_total_100_for_any_counts() -> None:
    rng = random.Random(42)
    for _ in range(500):
        counts = {i: rng.randint(0, 200) for i in (1, 2, 3)}
        if sum(counts.values()) == 0:
            continue
        assert sum(largest_remainder_percentages(counts).values()) == 100, counts


def test_result_is_the_same_every_time() -> None:
    counts = {1: 5, 2: 5, 3: 5}

    assert largest_remainder_percentages(counts) == largest_remainder_percentages(counts)


# --- what the response is allowed to contain ---------------------------------------------


def test_stats_models_carry_no_player_information() -> None:
    assert set(CrowdStats.model_fields) == {"available", "total_responses", "choices", "message"}
    assert set(ChoiceShare.model_fields) == {"choice_id", "label", "percent"}


# --- counting real answers ---------------------------------------------------------------


@pytest.fixture
def scenario(db: Session) -> Scenario:
    return add_scenario(db, add_category(db, "friendship"), "s1")


@pytest.fixture
def viewer(db: Session) -> User:
    return make_player(db, "viewer")


def crowd_answers(db: Session, scenario: Scenario, picks: list[int]) -> None:
    """One new player per pick, each completing a one-question round choosing option `pick`."""
    for index, pick in enumerate(picks):
        player = make_player(db, f"crowd{index}_{pick}")
        record_round(db, player, [(scenario, scenario.choices[pick])])


def stats(db: Session, scenario: Scenario, viewer: User, min_sample: int = 3) -> CrowdStats:
    return crowd_stats_for(db, [scenario], exclude_user_id=viewer.id, min_sample=min_sample)[
        scenario.id
    ]


def test_below_the_minimum_nothing_is_revealed(
    db: Session, scenario: Scenario, viewer: User
) -> None:
    crowd_answers(db, scenario, [0, 1])  # 2 responses, minimum is 3

    result = stats(db, scenario, viewer)

    assert result.available is False
    assert result.total_responses is None  # even the count stays hidden
    assert result.choices == []
    assert result.message == NOT_ENOUGH_RESPONSES == "Not enough responses yet."


def test_nobody_has_answered_yet(db: Session, scenario: Scenario, viewer: User) -> None:
    assert stats(db, scenario, viewer).available is False


def test_at_the_minimum_the_split_is_revealed(
    db: Session, scenario: Scenario, viewer: User
) -> None:
    crowd_answers(db, scenario, [0, 0, 1])

    result = stats(db, scenario, viewer)

    assert result.available is True
    assert result.total_responses == 3
    assert result.message is None
    assert [(c.label, c.percent) for c in result.choices] == [("A", 67), ("B", 33), ("C", 0)]
    assert sum(c.percent for c in result.choices) == 100


def test_every_option_is_listed_even_if_nobody_chose_it(
    db: Session, scenario: Scenario, viewer: User
) -> None:
    crowd_answers(db, scenario, [2, 2, 2])

    shares = {c.label: c.percent for c in stats(db, scenario, viewer).choices}

    assert shares == {"A": 0, "B": 0, "C": 100}


def test_the_requesting_players_own_answers_are_excluded(
    db: Session, scenario: Scenario, viewer: User
) -> None:
    record_round(db, viewer, [(scenario, scenario.choices[0])])  # the viewer's own vote
    crowd_answers(db, scenario, [1, 1])

    result = stats(db, scenario, viewer)

    assert result.available is False  # only 2 OTHER players, so still below the minimum


def test_own_answers_never_change_the_split(db: Session, scenario: Scenario, viewer: User) -> None:
    crowd_answers(db, scenario, [1, 1, 1])
    before = stats(db, scenario, viewer)

    record_round(db, viewer, [(scenario, scenario.choices[0])])

    assert stats(db, scenario, viewer) == before


@pytest.mark.parametrize("status", [RoundStatus.IN_PROGRESS, RoundStatus.ABANDONED])
def test_unfinished_rounds_do_not_count(
    db: Session, scenario: Scenario, viewer: User, status: RoundStatus
) -> None:
    for index in range(3):
        record_round(
            db, make_player(db, f"quitter{index}"), [(scenario, scenario.choices[0])], status=status
        )

    assert stats(db, scenario, viewer).available is False


def test_only_a_players_first_answer_counts(db: Session, scenario: Scenario, viewer: User) -> None:
    """Replaying a scenario and answering differently must not change the crowd."""
    replayer = make_player(db, "replayer")
    record_round(db, replayer, [(scenario, scenario.choices[0])], answered_at=T0)  # first: A
    record_round(
        db, replayer, [(scenario, scenario.choices[2])], answered_at=T0 + timedelta(days=1)
    )  # later: C
    crowd_answers(db, scenario, [0, 0])

    result = stats(db, scenario, viewer)

    assert result.total_responses == 3  # 3 players, not 4 answers
    assert {c.label: c.percent for c in result.choices} == {"A": 100, "B": 0, "C": 0}


def test_scenarios_are_counted_independently(db: Session, viewer: User) -> None:
    category = add_category(db, "money")
    first, second = add_scenario(db, category, "a"), add_scenario(db, category, "b")
    for index in range(3):
        record_round(
            db,
            make_player(db, f"p{index}"),
            [(first, first.choices[0]), (second, second.choices[2])],
        )

    result = crowd_stats_for(db, [first, second], exclude_user_id=viewer.id, min_sample=3)

    assert {c.label: c.percent for c in result[first.id].choices} == {"A": 100, "B": 0, "C": 0}
    assert {c.label: c.percent for c in result[second.id].choices} == {"A": 0, "B": 0, "C": 100}


def test_no_scenarios_gives_no_stats(db: Session, viewer: User) -> None:
    assert crowd_stats_for(db, [], exclude_user_id=viewer.id) == {}


def test_default_minimum_comes_from_settings(db: Session, scenario: Scenario, viewer: User) -> None:
    crowd_answers(db, scenario, [0, 1, 2])  # 3 responses; the default minimum is 20

    result = crowd_stats_for(db, [scenario], exclude_user_id=viewer.id)[scenario.id]

    assert result.available is False
