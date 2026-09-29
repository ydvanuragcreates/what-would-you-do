from collections.abc import Collection

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Category, Choice, Scenario
from app.db.models.enums import ScenarioStatus
from app.schemas.scenario import (
    CategoriesResponse,
    CategoryPublic,
    ChoicePublic,
    RandomOption,
    ScenarioPublic,
)

CHOICES_PER_SCENARIO = 3
LABELS = {1: "A", 2: "B", 3: "C"}


def _is_playable() -> ColumnElement[bool]:
    """Active AND has exactly 3 choices, so a half-built scenario never reaches a player."""
    choice_count = (
        select(func.count(Choice.id)).where(Choice.scenario_id == Scenario.id).scalar_subquery()
    )
    return (Scenario.status == ScenarioStatus.ACTIVE) & (choice_count == CHOICES_PER_SCENARIO)


def get_active_scenarios(
    db: Session,
    *,
    category_id: int | None = None,
    exclude_ids: Collection[int] = (),
) -> list[Scenario]:
    """Scenarios a player may be given, optionally limited to one category.

    `category_id=None` means "Random": every category. `exclude_ids` lets the game
    engine skip scenarios that are already used.
    """
    query = (
        select(Scenario)
        .where(_is_playable())
        .options(selectinload(Scenario.choices), selectinload(Scenario.category))
        .order_by(Scenario.id)
    )
    if category_id is not None:
        query = query.where(Scenario.category_id == category_id)
    if exclude_ids:
        query = query.where(Scenario.id.not_in(exclude_ids))
    return list(db.scalars(query))


def to_public(scenario: Scenario) -> ScenarioPublic:
    """The only way a Scenario becomes an API response. Weights are never copied across."""
    return ScenarioPublic(
        id=scenario.id,
        title=scenario.title,
        situation_text=scenario.situation_text,
        category=scenario.category.slug,
        choices=[
            ChoicePublic(id=choice.id, label=LABELS[choice.position], text=choice.choice_text)
            for choice in scenario.choices
        ],
    )


def list_categories(db: Session, *, round_length: int) -> CategoriesResponse:
    counts = dict(
        db.execute(
            select(Scenario.category_id, func.count(Scenario.id))
            .where(_is_playable())
            .group_by(Scenario.category_id)
        )
        .tuples()
        .all()
    )
    categories = db.scalars(select(Category).order_by(Category.sort_order, Category.name))
    total = sum(counts.values())
    return CategoriesResponse(
        round_length=round_length,
        random=RandomOption(scenario_count=total, playable=total >= round_length),
        categories=[
            CategoryPublic(
                id=category.id,
                slug=category.slug,
                name=category.name,
                emoji=category.emoji,
                scenario_count=counts.get(category.id, 0),
                playable=counts.get(category.id, 0) >= round_length,
            )
            for category in categories
        ],
    )
