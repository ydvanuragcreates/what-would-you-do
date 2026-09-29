"""Load scenario content from YAML files into the database.

Two steps, kept separate so the first can run without a database:

1. `load_seed`   reads and strictly validates every YAML file (raises SeedValidationError)
2. `apply_seed`  upserts the validated content, matching scenarios by `slug`

Rule enforced here: once players have answered a scenario, its situation text and
choices are frozen. Editing them would silently change what earlier answers meant
and corrupt the "how others answered" statistics. To change a scenario, retire the
old slug (`status: retired`) and add a new one.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Category, Choice, Scenario, UserAnswer
from app.db.models.enums import ScenarioSource, ScenarioStatus
from app.domain.dimensions import Dimension

# --- what a valid YAML file looks like -----------------------------------------------


class SeedCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=50)
    name: str = Field(min_length=1, max_length=100)
    emoji: str = Field(default="", max_length=16)
    sort_order: int = 0


class SeedChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Short on purpose: players read this on a phone, mid-game.
    text: str = Field(min_length=1, max_length=140)
    weights: dict[Dimension, Annotated[int, Field(ge=0, le=10)]]

    @field_validator("weights")
    @classmethod
    def weight_one_to_four_dimensions(cls, weights: dict[Dimension, int]) -> dict[Dimension, int]:
        if not 1 <= len(weights) <= 4:
            raise ValueError("a choice must weight between 1 and 4 dimensions")
        return weights


class SeedScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=100)
    title: str = Field(min_length=1, max_length=60)
    difficulty: int = Field(ge=1, le=3)  # 1 light, 2 uncomfortable, 3 heavy
    status: ScenarioStatus = ScenarioStatus.ACTIVE
    situation: str = Field(min_length=1, max_length=400)
    choices: list[SeedChoice] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def all_choices_weight_the_same_dimensions(self) -> "SeedScenario":
        # Otherwise dodging the choice that carries a dimension would erase that
        # dimension from the player's profile, instead of scoring it low.
        measured = [frozenset(choice.weights) for choice in self.choices]
        if len(set(measured)) != 1:
            raise ValueError("all 3 choices must weight exactly the same set of dimensions")

        # A dimension that scores the same whatever you pick measures nothing.
        for dimension in self.choices[0].weights:
            values = [choice.weights[dimension] for choice in self.choices]
            if max(values) - min(values) < 2:
                raise ValueError(
                    f"'{dimension.value}' barely differs between the choices {values}; "
                    "drop it from this scenario or make the choices differ on it"
                )
        return self


class SeedFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    scenarios: list[SeedScenario]


# --- step 1: read and validate --------------------------------------------------------


class SeedValidationError(Exception):
    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("\n".join(problems))


@dataclass
class SeedData:
    categories: list[SeedCategory]
    scenarios: list[tuple[str, SeedScenario]]  # (category slug, scenario)


def load_seed(seed_dir: Path) -> SeedData:
    """Read every YAML file under `seed_dir` and report ALL problems at once."""
    problems: list[str] = []

    categories = _parse_categories(seed_dir / "categories.yaml", problems)
    known_categories = {category.slug for category in categories}

    scenarios: list[tuple[str, SeedScenario]] = []
    seen_slugs: dict[str, str] = {}
    for path in sorted((seed_dir / "scenarios").glob("*.yaml")):
        seed_file = _parse_file(path, problems)
        if seed_file is None:
            continue
        if seed_file.category not in known_categories:
            problems.append(f"{path.name}: unknown category '{seed_file.category}'")
        for scenario in seed_file.scenarios:
            if scenario.slug in seen_slugs:
                first_file = seen_slugs[scenario.slug]
                problems.append(f"{path.name}: slug '{scenario.slug}' already used in {first_file}")
            seen_slugs[scenario.slug] = path.name
            scenarios.append((seed_file.category, scenario))

    if problems:
        raise SeedValidationError(problems)
    return SeedData(categories=categories, scenarios=scenarios)


def _parse_categories(path: Path, problems: list[str]) -> list[SeedCategory]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        categories = [SeedCategory.model_validate(item) for item in raw]
    except (OSError, yaml.YAMLError, TypeError) as error:
        problems.append(f"{path.name}: cannot read ({error})")
        return []
    except ValidationError as error:
        problems.extend(_format(path.name, error))
        return []
    slugs = [category.slug for category in categories]
    if len(slugs) != len(set(slugs)):
        problems.append(f"{path.name}: duplicate category slug")
    return categories


def _parse_file(path: Path, problems: list[str]) -> SeedFile | None:
    try:
        return SeedFile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (OSError, yaml.YAMLError) as error:
        problems.append(f"{path.name}: cannot read ({error})")
    except ValidationError as error:
        problems.extend(_format(path.name, error))
    return None


def _format(filename: str, error: ValidationError) -> list[str]:
    return [
        f"{filename}: {'.'.join(str(part) for part in e['loc'])}: {e['msg']}"
        for e in error.errors()
    ]


# --- step 2: write to the database ------------------------------------------------------


@dataclass
class SeedReport:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: int = 0
    # Wanted a change to text/choices, but players already answered: needs a new slug.
    blocked: list[str] = field(default_factory=list)


def apply_seed(db: Session, data: SeedData) -> SeedReport:
    """Create or update categories and scenarios, then commit once. Never deletes anything."""
    report = SeedReport()
    categories = _upsert_categories(db, data.categories)
    existing = {
        scenario.slug: scenario
        for scenario in db.scalars(select(Scenario).options(selectinload(Scenario.choices)))
    }
    answered = set(db.scalars(select(UserAnswer.scenario_id).distinct()))

    for category_slug, item in data.scenarios:
        category = categories[category_slug]
        current = existing.get(item.slug)

        if current is None:
            db.add(_new_scenario(item, category))
            report.created.append(item.slug)
        elif _frozen_content_differs(current, item) and current.id in answered:
            _update_metadata(current, item, category)  # title/category/status are always safe
            report.blocked.append(item.slug)
        elif _frozen_content_differs(current, item) or _metadata_differs(current, item, category):
            _update_scenario(current, item, category)
            report.updated.append(item.slug)
        else:
            report.unchanged += 1

    db.commit()
    return report


def _upsert_categories(db: Session, wanted: list[SeedCategory]) -> dict[str, Category]:
    by_slug = {category.slug: category for category in db.scalars(select(Category))}
    for item in wanted:
        category = by_slug.get(item.slug)
        if category is None:
            category = Category(slug=item.slug)
            db.add(category)
            by_slug[item.slug] = category
        category.name = item.name
        category.emoji = item.emoji
        category.sort_order = item.sort_order
    db.flush()  # assigns ids to new categories
    return by_slug


def _weights_json(choice: SeedChoice) -> dict[str, int]:
    return {dimension.value: weight for dimension, weight in choice.weights.items()}


def _new_scenario(item: SeedScenario, category: Category) -> Scenario:
    return Scenario(
        slug=item.slug,
        title=item.title,
        situation_text=item.situation,
        category_id=category.id,
        difficulty=item.difficulty,
        status=item.status,
        source=ScenarioSource.MANUAL,
        choices=[
            Choice(position=position, choice_text=choice.text, weights=_weights_json(choice))
            for position, choice in enumerate(item.choices, start=1)
        ],
    )


def _frozen_content_differs(current: Scenario, item: SeedScenario) -> bool:
    if current.situation_text != item.situation:
        return True
    stored = [(choice.choice_text, choice.weights) for choice in current.choices]
    wanted = [(choice.text, _weights_json(choice)) for choice in item.choices]
    return stored != wanted


def _metadata_differs(current: Scenario, item: SeedScenario, category: Category) -> bool:
    return (
        current.title != item.title
        or current.difficulty != item.difficulty
        or current.status != item.status
        or current.category_id != category.id
    )


def _update_metadata(current: Scenario, item: SeedScenario, category: Category) -> None:
    current.title = item.title
    current.difficulty = item.difficulty
    current.status = item.status
    current.category_id = category.id


def _update_scenario(current: Scenario, item: SeedScenario, category: Category) -> None:
    _update_metadata(current, item, category)
    current.situation_text = item.situation
    for stored, wanted in zip(current.choices, item.choices, strict=True):
        stored.choice_text = wanted.text
        stored.weights = _weights_json(wanted)
