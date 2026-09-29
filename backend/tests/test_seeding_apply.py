from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Category, Round, RoundQuestion, Scenario, User, UserAnswer
from app.db.models.enums import ScenarioSource, ScenarioStatus
from app.services.seeding import SeedData, apply_seed, load_seed
from tests.seed_helpers import scenario_dict, write_seed


def seed(tmp_path: Path, **files: list[dict]) -> SeedData:  # type: ignore[type-arg]
    return load_seed(write_seed(tmp_path, files))


def get_scenario(db: Session, slug: str) -> Scenario:
    return db.scalars(select(Scenario).where(Scenario.slug == slug)).one()


def record_an_answer(db: Session, scenario: Scenario) -> None:
    """Make it look like a player has answered this scenario."""
    user = User(username="Player", email="player@example.com", password_hash="x")
    db.add(user)
    db.flush()
    round_ = Round(user_id=user.id, question_count=1)
    round_.questions = [RoundQuestion(scenario_id=scenario.id, question_order=1)]
    db.add(round_)
    db.flush()
    db.add(
        UserAnswer(round_id=round_.id, scenario_id=scenario.id, choice_id=scenario.choices[0].id)
    )
    db.flush()


def test_first_run_creates_everything(db: Session, tmp_path: Path) -> None:
    data = seed(tmp_path, friendship=[scenario_dict("one"), scenario_dict("two")])

    report = apply_seed(db, data)

    assert sorted(report.created) == ["one", "two"]
    scenario = get_scenario(db, "one")
    assert scenario.status == ScenarioStatus.ACTIVE
    assert scenario.source == ScenarioSource.MANUAL
    assert scenario.category.slug == "friendship"
    assert [c.position for c in scenario.choices] == [1, 2, 3]
    # weights are stored as plain JSON with string keys
    assert scenario.choices[0].weights == {"honesty": 9, "loyalty": 2}


def test_running_twice_changes_nothing(db: Session, tmp_path: Path) -> None:
    data = seed(tmp_path, friendship=[scenario_dict("one")])
    apply_seed(db, data)

    report = apply_seed(db, data)

    assert (report.created, report.updated, report.blocked) == ([], [], [])
    assert report.unchanged == 1
    assert db.scalar(select(func.count(Scenario.id))) == 1


def test_unanswered_scenario_can_be_edited(db: Session, tmp_path: Path) -> None:
    apply_seed(db, seed(tmp_path / "v1", friendship=[scenario_dict("one")]))

    edited = scenario_dict("one", situation="A completely rewritten situation.")
    report = apply_seed(db, seed(tmp_path / "v2", friendship=[edited]))

    assert report.updated == ["one"]
    assert get_scenario(db, "one").situation_text == "A completely rewritten situation."


def test_answered_scenario_text_is_frozen(db: Session, tmp_path: Path) -> None:
    """Changing the wording after people answered would corrupt the crowd statistics."""
    apply_seed(db, seed(tmp_path / "v1", friendship=[scenario_dict("one")]))
    record_an_answer(db, get_scenario(db, "one"))

    edited = scenario_dict("one", title="New title", situation="Sneakily different wording.")
    report = apply_seed(db, seed(tmp_path / "v2", friendship=[edited]))

    assert report.blocked == ["one"]
    scenario = get_scenario(db, "one")
    assert scenario.situation_text == "Something happens and you must decide what to do."
    assert scenario.title == "New title"  # harmless metadata is still updated


def test_answered_scenario_weights_are_frozen(db: Session, tmp_path: Path) -> None:
    apply_seed(db, seed(tmp_path / "v1", friendship=[scenario_dict("one")]))
    record_an_answer(db, get_scenario(db, "one"))

    choices = scenario_dict()["choices"]
    choices[0]["weights"] = {"honesty": 7, "loyalty": 1}
    report = apply_seed(
        db, seed(tmp_path / "v2", friendship=[scenario_dict("one", choices=choices)])
    )

    assert report.blocked == ["one"]
    assert get_scenario(db, "one").choices[0].weights == {"honesty": 9, "loyalty": 2}


def test_answered_scenario_can_still_be_retired(db: Session, tmp_path: Path) -> None:
    apply_seed(db, seed(tmp_path / "v1", friendship=[scenario_dict("one")]))
    record_an_answer(db, get_scenario(db, "one"))

    report = apply_seed(
        db, seed(tmp_path / "v2", friendship=[scenario_dict("one", status="retired")])
    )

    assert report.updated == ["one"]
    assert get_scenario(db, "one").status == ScenarioStatus.RETIRED


def test_scenarios_missing_from_the_files_are_never_deleted(db: Session, tmp_path: Path) -> None:
    apply_seed(db, seed(tmp_path / "v1", friendship=[scenario_dict("one"), scenario_dict("two")]))

    apply_seed(db, seed(tmp_path / "v2", friendship=[scenario_dict("one")]))

    assert db.scalar(select(func.count(Scenario.id))) == 2


def test_scenario_can_move_category(db: Session, tmp_path: Path) -> None:
    apply_seed(db, seed(tmp_path / "v1", friendship=[scenario_dict("one")]))

    apply_seed(db, seed(tmp_path / "v2", money=[scenario_dict("one")]))

    assert get_scenario(db, "one").category.slug == "money"
    assert db.scalar(select(func.count(Category.id))) == 2
