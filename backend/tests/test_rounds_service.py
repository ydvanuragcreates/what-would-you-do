import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import (
    InvalidChoiceError,
    NotCurrentQuestionError,
    NotEnoughScenariosError,
    RoundNotFoundError,
    RoundNotInProgressError,
)
from app.db.models import Category, RoundQuestion, Scenario, User
from app.db.models.enums import RoundStatus
from app.services import rounds as service
from tests.test_scenarios_service import add_category, add_scenario


def add_user(db: Session, username: str = "player") -> User:
    user = User(username=username, email=f"{username}@example.com", password_hash="x")
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def player(db: Session) -> User:
    return add_user(db)


@pytest.fixture
def friendship(db: Session) -> Category:
    return add_category(db, "friendship")


# --- starting a round ---------------------------------------------------------------


def test_start_round_creates_ordered_questions(
    db: Session, player: User, friendship: Category
) -> None:
    for i in range(3):
        add_scenario(db, friendship, f"f{i}")

    state = service.start_round(db, user_id=player.id, category_id=None, round_length=3)

    round_id = state.id
    questions = db.scalars(
        select(RoundQuestion)
        .where(RoundQuestion.round_id == round_id)
        .order_by(RoundQuestion.question_order)
    ).all()
    assert [q.question_order for q in questions] == [1, 2, 3]
    assert len({q.scenario_id for q in questions}) == 3  # no duplicates
    assert state.status == RoundStatus.IN_PROGRESS
    assert state.question_count == 3
    assert state.current_question_number == 1
    assert state.question is not None
    assert state.result is None


def test_start_round_scopes_to_category(db: Session, player: User, friendship: Category) -> None:
    money = add_category(db, "money")
    for i in range(2):
        add_scenario(db, friendship, f"f{i}")
    add_scenario(db, money, "m0")

    state = service.start_round(db, user_id=player.id, category_id=friendship.id, round_length=2)

    scenario_ids = db.scalars(
        select(RoundQuestion.scenario_id).where(RoundQuestion.round_id == state.id)
    ).all()
    categories = db.scalars(select(Scenario.category_id).where(Scenario.id.in_(scenario_ids))).all()
    assert set(categories) == {friendship.id}


def test_start_round_not_enough_scenarios_raises(
    db: Session, player: User, friendship: Category
) -> None:
    add_scenario(db, friendship, "f0")

    with pytest.raises(NotEnoughScenariosError):
        service.start_round(db, user_id=player.id, category_id=None, round_length=3)


# --- answering -----------------------------------------------------------------------


def test_answer_advances_to_next_question(db: Session, player: User, friendship: Category) -> None:
    for i in range(3):
        add_scenario(db, friendship, f"f{i}")
    state = service.start_round(db, user_id=player.id, category_id=None, round_length=3)
    first_question = state.question
    assert first_question is not None
    choice_id = first_question.choices[0].id

    next_state = service.submit_answer(
        db,
        round_id=state.id,
        user_id=player.id,
        scenario_id=first_question.id,
        choice_id=choice_id,
    )

    assert next_state.status == RoundStatus.IN_PROGRESS
    assert next_state.current_question_number == 2
    assert next_state.question is not None
    assert next_state.question.id != first_question.id


def test_wrong_scenario_raises(db: Session, player: User, friendship: Category) -> None:
    for i in range(3):
        add_scenario(db, friendship, f"f{i}")
    state = service.start_round(db, user_id=player.id, category_id=None, round_length=3)
    assert state.question is not None
    all_scenario_ids = db.scalars(
        select(RoundQuestion.scenario_id).where(RoundQuestion.round_id == state.id)
    ).all()
    not_current_id = next(sid for sid in all_scenario_ids if sid != state.question.id)
    not_current_scenario = db.get(Scenario, not_current_id)
    assert not_current_scenario is not None
    choice_id = not_current_scenario.choices[0].id

    with pytest.raises(NotCurrentQuestionError):
        service.submit_answer(
            db,
            round_id=state.id,
            user_id=player.id,
            scenario_id=not_current_id,
            choice_id=choice_id,
        )


def test_already_answered_question_raises(db: Session, player: User, friendship: Category) -> None:
    for i in range(3):
        add_scenario(db, friendship, f"f{i}")
    state = service.start_round(db, user_id=player.id, category_id=None, round_length=3)
    first_question = state.question
    assert first_question is not None
    choice_id = first_question.choices[0].id
    service.submit_answer(
        db, round_id=state.id, user_id=player.id, scenario_id=first_question.id, choice_id=choice_id
    )

    with pytest.raises(NotCurrentQuestionError):
        service.submit_answer(
            db,
            round_id=state.id,
            user_id=player.id,
            scenario_id=first_question.id,
            choice_id=choice_id,
        )


def test_invalid_choice_raises(db: Session, player: User, friendship: Category) -> None:
    add_scenario(db, friendship, "f0")
    add_scenario(db, friendship, "f1")
    add_scenario(db, friendship, "f2")
    state = service.start_round(db, user_id=player.id, category_id=None, round_length=3)
    first_question = state.question
    assert first_question is not None
    other_scenario_id = next(
        sid
        for sid in db.scalars(
            select(RoundQuestion.scenario_id).where(RoundQuestion.round_id == state.id)
        ).all()
        if sid != first_question.id
    )
    other_scenario = db.get(Scenario, other_scenario_id)
    assert other_scenario is not None
    choice_from_other_scenario = other_scenario.choices[0].id

    with pytest.raises(InvalidChoiceError):
        service.submit_answer(
            db,
            round_id=state.id,
            user_id=player.id,
            scenario_id=first_question.id,
            choice_id=choice_from_other_scenario,
        )


def test_not_your_round_raises(db: Session, player: User, friendship: Category) -> None:
    intruder = add_user(db, "intruder")
    add_scenario(db, friendship, "f0")
    add_scenario(db, friendship, "f1")
    add_scenario(db, friendship, "f2")
    state = service.start_round(db, user_id=player.id, category_id=None, round_length=3)

    with pytest.raises(RoundNotFoundError):
        service.get_round_state(db, round_id=state.id, user_id=intruder.id)


def test_round_not_in_progress_raises(db: Session, player: User, friendship: Category) -> None:
    add_scenario(db, friendship, "f0")
    add_scenario(db, friendship, "f1")
    add_scenario(db, friendship, "f2")
    state = service.start_round(db, user_id=player.id, category_id=None, round_length=3)
    for _ in range(3):
        question = state.question
        assert question is not None
        state = service.submit_answer(
            db,
            round_id=state.id,
            user_id=player.id,
            scenario_id=question.id,
            choice_id=question.choices[0].id,
        )
    assert state.status == RoundStatus.COMPLETED

    with pytest.raises(RoundNotInProgressError):
        service.submit_answer(db, round_id=state.id, user_id=player.id, scenario_id=1, choice_id=1)


# --- completion & scoring --------------------------------------------------------------


def test_full_playthrough_completes_with_scored_result(
    db: Session, player: User, friendship: Category
) -> None:
    for i in range(3):
        add_scenario(db, friendship, f"f{i}")
    state = service.start_round(db, user_id=player.id, category_id=None, round_length=3)

    # Always pick position-1 (weights honesty=1, loyalty=8, identical across scenarios,
    # see add_scenario in tests/test_scenarios_service.py), so the expected result is
    # the same regardless of which scenarios/order random.sample picked.
    for _ in range(3):
        question = state.question
        assert question is not None
        assert state.status == RoundStatus.IN_PROGRESS
        state = service.submit_answer(
            db,
            round_id=state.id,
            user_id=player.id,
            scenario_id=question.id,
            choice_id=question.choices[0].id,
        )

    assert state.status == RoundStatus.COMPLETED
    assert state.current_question_number is None
    assert state.question is None
    assert state.result is not None
    assert state.result.scores == {"honesty": 1.0, "loyalty": 8.0}
    assert state.result.profile_key == "devoted-ally"

    final = service.get_round_state(db, round_id=state.id, user_id=player.id)
    assert final.status == RoundStatus.COMPLETED
    assert final.result == state.result
