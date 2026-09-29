import json

import pytest
from sqlalchemy.orm import Session

from app.db.models import Category, Choice, Scenario
from app.db.models.enums import ScenarioStatus
from app.domain.dimensions import Dimension
from app.schemas.scenario import CategoryPublic, ChoicePublic, ScenarioPublic
from app.services import scenarios as service


def add_category(db: Session, slug: str) -> Category:
    category = Category(slug=slug, name=slug.title(), sort_order=len(slug))
    db.add(category)
    db.flush()
    return category


def add_scenario(
    db: Session,
    category: Category,
    slug: str,
    *,
    status: ScenarioStatus = ScenarioStatus.ACTIVE,
    choice_count: int = 3,
) -> Scenario:
    scenario = Scenario(
        slug=slug,
        title=slug,
        situation_text="Text.",
        category_id=category.id,
        status=status,
        choices=[
            Choice(
                position=i,
                choice_text=f"{slug} option {i}",
                weights={"honesty": i, "loyalty": 9 - i},
            )
            for i in range(1, choice_count + 1)
        ],
    )
    db.add(scenario)
    db.flush()
    return scenario


@pytest.fixture
def friendship(db: Session) -> Category:
    return add_category(db, "friendship")


@pytest.fixture
def money(db: Session) -> Category:
    return add_category(db, "money")


# --- retrieval ---------------------------------------------------------------------


def test_only_active_complete_scenarios_are_playable(db: Session, friendship: Category) -> None:
    add_scenario(db, friendship, "good")
    add_scenario(db, friendship, "draft", status=ScenarioStatus.DRAFT)
    add_scenario(db, friendship, "retired", status=ScenarioStatus.RETIRED)
    add_scenario(db, friendship, "incomplete", choice_count=2)

    slugs = [s.slug for s in service.get_active_scenarios(db)]

    assert slugs == ["good"]


def test_category_filter(db: Session, friendship: Category, money: Category) -> None:
    add_scenario(db, friendship, "f1")
    add_scenario(db, friendship, "f2")
    add_scenario(db, money, "m1")

    assert [s.slug for s in service.get_active_scenarios(db, category_id=friendship.id)] == [
        "f1",
        "f2",
    ]
    assert [s.slug for s in service.get_active_scenarios(db, category_id=money.id)] == ["m1"]
    assert len(service.get_active_scenarios(db)) == 3  # None means Random: every category


def test_exclude_ids(db: Session, friendship: Category) -> None:
    first = add_scenario(db, friendship, "f1")
    add_scenario(db, friendship, "f2")

    result = service.get_active_scenarios(db, exclude_ids={first.id})

    assert [s.slug for s in result] == ["f2"]


def test_choices_come_back_in_order(db: Session, friendship: Category) -> None:
    add_scenario(db, friendship, "f1")
    db.expire_all()

    scenario = service.get_active_scenarios(db)[0]

    assert [c.position for c in scenario.choices] == [1, 2, 3]


# --- the public view never carries scoring data ---------------------------------------


def test_public_schemas_have_no_scoring_fields() -> None:
    assert set(ChoicePublic.model_fields) == {"id", "label", "text"}
    assert set(ScenarioPublic.model_fields) == {
        "id",
        "title",
        "situation_text",
        "category",
        "choices",
    }


def test_public_scenario_json_contains_no_weights(db: Session, friendship: Category) -> None:
    add_scenario(db, friendship, "f1")
    scenario = service.get_active_scenarios(db)[0]

    public = service.to_public(scenario)
    dumped = json.dumps(public.model_dump())

    assert [c.label for c in public.choices] == ["A", "B", "C"]
    assert "weight" not in dumped.lower()
    for dimension in Dimension:
        assert f'"{dimension.value}"' not in dumped


# --- category listing ----------------------------------------------------------------


def test_category_counts_and_playable_flag(
    db: Session, friendship: Category, money: Category
) -> None:
    add_scenario(db, friendship, "f1")
    add_scenario(db, friendship, "f2")
    add_scenario(db, money, "m1")
    add_scenario(db, money, "hidden", status=ScenarioStatus.DRAFT)  # must not be counted

    result = service.list_categories(db, round_length=2)

    by_slug: dict[str, CategoryPublic] = {c.slug: c for c in result.categories}
    assert by_slug["friendship"].scenario_count == 2
    assert by_slug["friendship"].playable is True
    assert by_slug["money"].scenario_count == 1
    assert by_slug["money"].playable is False
    assert result.random.scenario_count == 3
    assert result.random.playable is True
    assert result.round_length == 2


def test_empty_category_is_listed_but_not_playable(db: Session, friendship: Category) -> None:
    result = service.list_categories(db, round_length=10)

    assert result.categories[0].scenario_count == 0
    assert result.categories[0].playable is False
    assert result.random.playable is False
