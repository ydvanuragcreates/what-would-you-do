import random
from collections import Counter
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RoundQuestion, Scenario
from app.domain.selection import Candidate, select_scenarios
from app.services import rounds as service
from tests.test_rounds_service import add_user
from tests.test_scenarios_service import add_category, add_scenario

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def pick(
    candidates: list[Candidate],
    last_seen: dict[int, datetime] | None = None,
    count: int = 5,
    seed: int = 1,
    spread: bool = False,
) -> list[int]:
    return select_scenarios(
        candidates, last_seen or {}, count, random.Random(seed), spread_categories=spread
    )


def candidates(per_category: dict[int, int]) -> list[Candidate]:
    """{category id: how many scenarios}, with unique scenario ids."""
    result: list[Candidate] = []
    for category_id, how_many in per_category.items():
        first_id = len(result) + 1  # computed up front: extend() consumes a lazy generator
        result.extend(Candidate(first_id + i, category_id) for i in range(how_many))
    return result


# --- pure selection rules ----------------------------------------------------------------


def test_returns_the_requested_number_of_distinct_scenarios() -> None:
    picked = pick(candidates({1: 20}), count=10)

    assert len(picked) == 10
    assert len(set(picked)) == 10


def test_same_seed_gives_the_same_round() -> None:
    pool = candidates({1: 10, 2: 10})

    assert pick(pool, seed=7, spread=True) == pick(pool, seed=7, spread=True)


def test_unseen_scenarios_are_always_preferred() -> None:
    pool = candidates({1: 10})
    seen = {c.id: T0 for c in pool[:4]}  # 4 seen, 6 unseen

    for seed in range(20):
        picked = pick(pool, seen, count=5, seed=seed)
        assert not set(picked) & set(seen), "picked a seen scenario while unseen ones remained"


def test_tops_up_with_the_longest_ago_seen_when_unseen_run_out() -> None:
    pool = candidates({1: 10})
    unseen_ids = {pool[0].id, pool[1].id}
    # ids 3..10 were seen, id 3 longest ago, id 10 most recently
    seen = {c.id: T0 + timedelta(days=c.id) for c in pool[2:]}

    picked = pick(pool, seen, count=5)

    assert set(picked) == unseen_ids | {3, 4, 5}


def test_picking_everything_when_pool_equals_round_length() -> None:
    pool = candidates({1: 3})

    assert sorted(pick(pool, {c.id: T0 for c in pool}, count=3)) == [1, 2, 3]


def test_too_few_candidates_is_an_error() -> None:
    with pytest.raises(ValueError):
        pick(candidates({1: 2}), count=3)


@pytest.mark.parametrize("seed", range(10))
def test_spread_gives_each_category_an_equal_share(seed: int) -> None:
    pool = candidates({1: 8, 2: 8, 3: 8})

    picked = pick(pool, count=6, seed=seed, spread=True)

    by_category = Counter(next(c.category_id for c in pool if c.id == i) for i in picked)
    assert by_category == {1: 2, 2: 2, 3: 2}


def test_spread_with_uneven_categories_takes_what_it_can() -> None:
    pool = candidates({1: 1, 2: 10})  # category 1 has a single scenario

    picked = pick(pool, count=4, spread=True)

    by_category = Counter(next(c.category_id for c in pool if c.id == i) for i in picked)
    assert by_category == {1: 1, 2: 3}


def test_spread_still_prefers_unseen_over_balance() -> None:
    pool = candidates({1: 5, 2: 5})
    seen = {c.id: T0 for c in pool if c.category_id == 1}  # all of category 1 already seen

    picked = pick(pool, seen, count=4, spread=True)

    assert all(next(c.category_id for c in pool if c.id == i) == 2 for i in picked)


# --- against the real database -------------------------------------------------------------


def answer_whole_round(db: Session, user_id, state) -> None:  # type: ignore[no-untyped-def]
    while state.question is not None:
        state = service.submit_answer(
            db,
            round_id=state.id,
            user_id=user_id,
            scenario_id=state.question.id,
            choice_id=state.question.choices[0].id,
        )


def round_scenario_ids(db: Session, round_id) -> set[int]:  # type: ignore[no-untyped-def]
    return set(
        db.scalars(select(RoundQuestion.scenario_id).where(RoundQuestion.round_id == round_id))
    )


def test_next_round_uses_scenarios_the_player_has_not_seen(db: Session) -> None:
    player = add_user(db)
    category = add_category(db, "friendship")
    for i in range(6):
        add_scenario(db, category, f"f{i}")

    first = service.start_round(db, user_id=player.id, category_id=None, round_length=3)
    first_ids = round_scenario_ids(db, first.id)
    answer_whole_round(db, player.id, first)

    second = service.start_round(db, user_id=player.id, category_id=None, round_length=3)

    assert not round_scenario_ids(db, second.id) & first_ids


def test_when_everything_was_seen_a_round_still_starts(db: Session) -> None:
    player = add_user(db)
    category = add_category(db, "friendship")
    for i in range(3):
        add_scenario(db, category, f"f{i}")
    first = service.start_round(db, user_id=player.id, category_id=None, round_length=3)
    answer_whole_round(db, player.id, first)

    second = service.start_round(db, user_id=player.id, category_id=None, round_length=3)

    assert len(round_scenario_ids(db, second.id)) == 3


def test_other_players_history_does_not_affect_selection(db: Session) -> None:
    veteran, newcomer = add_user(db, "veteran"), add_user(db, "newcomer")
    category = add_category(db, "friendship")
    for i in range(6):
        add_scenario(db, category, f"f{i}")
    first = service.start_round(db, user_id=veteran.id, category_id=None, round_length=3)
    answer_whole_round(db, veteran.id, first)
    seen_by_veteran = round_scenario_ids(db, first.id)

    # Across many rounds the newcomer must sometimes be given what the veteran saw.
    given: set[int] = set()
    for seed in range(15):
        state = service.start_round(
            db, user_id=newcomer.id, category_id=None, round_length=3, rng=random.Random(seed)
        )
        given |= round_scenario_ids(db, state.id)

    assert seen_by_veteran <= given


def test_random_round_is_spread_across_categories(db: Session) -> None:
    player = add_user(db)
    friendship, money = add_category(db, "friendship"), add_category(db, "money")
    for i in range(5):
        add_scenario(db, friendship, f"f{i}")
        add_scenario(db, money, f"m{i}")

    state = service.start_round(db, user_id=player.id, category_id=None, round_length=4)

    ids = round_scenario_ids(db, state.id)
    per_category = Counter(db.scalars(select(Scenario.category_id).where(Scenario.id.in_(ids))))
    assert len(ids) == 4
    assert sorted(per_category.values()) == [2, 2]
