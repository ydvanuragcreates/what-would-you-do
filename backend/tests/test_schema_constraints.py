"""The database itself must reject impossible data, even if a service has a bug.

These tests insert deliberately bad rows and expect PostgreSQL to refuse them.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    Category,
    Choice,
    Round,
    RoundQuestion,
    Scenario,
    User,
    UserAnswer,
)
from app.db.models.enums import ScenarioStatus


def make_scenario(db: Session, category: Category, slug: str) -> Scenario:
    scenario = Scenario(
        slug=slug,
        title=slug,
        situation_text="A short situation.",
        category_id=category.id,
        status=ScenarioStatus.ACTIVE,
        choices=[
            Choice(position=i, choice_text=f"Option {i}", weights={"honesty": i * 3})
            for i in (1, 2, 3)
        ],
    )
    db.add(scenario)
    db.flush()
    return scenario


@pytest.fixture
def category(db: Session) -> Category:
    category = Category(slug=f"friendship-{uuid.uuid4().hex[:6]}", name="Friendship")
    db.add(category)
    db.flush()
    return category


@pytest.fixture
def user(db: Session) -> User:
    user = User(username="Anna", email="anna@example.com", password_hash="x")
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def game(db: Session, category: Category, user: User) -> tuple[Round, Scenario, Scenario]:
    """A round containing scenario_a (question 1); scenario_b exists but is NOT in the round."""
    scenario_a = make_scenario(db, category, "a")
    scenario_b = make_scenario(db, category, "b")
    round_ = Round(user_id=user.id, question_count=1)
    round_.questions = [RoundQuestion(scenario_id=scenario_a.id, question_order=1)]
    db.add(round_)
    db.flush()
    return round_, scenario_a, scenario_b


def assert_rejected(db: Session, constraint: str, *rows: object) -> None:
    """Expect the database to refuse these rows because of this specific constraint.

    Checking the constraint name (not just "some error") stops a test from passing
    for the wrong reason. begin_nested() keeps the test's session usable afterwards.
    """
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.add_all(rows)
        db.flush()
    assert error.value.orig.diag.constraint_name == constraint  # type: ignore[union-attr]


def test_valid_answer_is_accepted(db: Session, game: tuple[Round, Scenario, Scenario]) -> None:
    round_, scenario_a, _ = game
    db.add(
        UserAnswer(
            round_id=round_.id, scenario_id=scenario_a.id, choice_id=scenario_a.choices[0].id
        )
    )
    db.flush()  # no exception == accepted


def test_same_question_cannot_be_answered_twice(
    db: Session, game: tuple[Round, Scenario, Scenario]
) -> None:
    round_, scenario_a, _ = game
    db.add(
        UserAnswer(
            round_id=round_.id, scenario_id=scenario_a.id, choice_id=scenario_a.choices[0].id
        )
    )
    db.flush()

    assert_rejected(
        db,
        "uq_user_answers_round_id_scenario_id",
        UserAnswer(
            round_id=round_.id, scenario_id=scenario_a.id, choice_id=scenario_a.choices[1].id
        ),
    )


def test_cannot_answer_a_scenario_that_is_not_in_the_round(
    db: Session, game: tuple[Round, Scenario, Scenario]
) -> None:
    round_, _, scenario_b = game

    assert_rejected(
        db,
        "fk_user_answers_round_question",
        UserAnswer(
            round_id=round_.id, scenario_id=scenario_b.id, choice_id=scenario_b.choices[0].id
        ),
    )


def test_choice_must_belong_to_the_answered_scenario(
    db: Session, game: tuple[Round, Scenario, Scenario]
) -> None:
    round_, scenario_a, scenario_b = game

    # Scenario A is in the round, but the choice comes from scenario B.
    assert_rejected(
        db,
        "fk_user_answers_choice_in_scenario",
        UserAnswer(
            round_id=round_.id, scenario_id=scenario_a.id, choice_id=scenario_b.choices[0].id
        ),
    )


def test_choice_position_must_be_1_to_3(db: Session, category: Category) -> None:
    scenario = make_scenario(db, category, "pos")

    assert_rejected(
        db,
        "ck_choices_position_range",
        Choice(scenario_id=scenario.id, position=4, choice_text="?", weights={}),
    )


def test_scenario_cannot_have_two_choices_in_the_same_slot(db: Session, category: Category) -> None:
    scenario = make_scenario(db, category, "slot")

    assert_rejected(
        db,
        "uq_choices_scenario_id_position",
        Choice(scenario_id=scenario.id, position=1, choice_text="dup", weights={}),
    )


def test_scenario_cannot_appear_twice_in_a_round(
    db: Session, game: tuple[Round, Scenario, Scenario]
) -> None:
    round_, scenario_a, _ = game

    assert_rejected(
        db,
        "uq_round_questions_round_id_scenario_id",
        RoundQuestion(round_id=round_.id, scenario_id=scenario_a.id, question_order=2),
    )


def test_difficulty_must_be_1_to_3(db: Session, category: Category) -> None:
    assert_rejected(
        db,
        "ck_scenarios_difficulty_range",
        Scenario(slug="hard", title="t", situation_text="s", category_id=category.id, difficulty=9),
    )


def test_username_and_email_are_unique_ignoring_case(db: Session, user: User) -> None:
    assert_rejected(
        db,
        "uq_users_username_lower",
        User(username="ANNA", email="other@example.com", password_hash="x"),
    )
    assert_rejected(
        db,
        "uq_users_email_lower",
        User(username="Someone", email="ANNA@example.com", password_hash="x"),
    )
