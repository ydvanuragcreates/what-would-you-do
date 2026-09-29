"""The seed validator must reject bad content clearly. No database needed."""

from pathlib import Path
from typing import Any

import pytest

from app.services.seeding import SeedValidationError, load_seed
from tests.seed_helpers import scenario_dict, write_seed


def problems_for(tmp_path: Path, scenario: dict[str, Any]) -> str:
    seed_dir = write_seed(tmp_path, {"friendship": [scenario]})
    with pytest.raises(SeedValidationError) as error:
        load_seed(seed_dir)
    return "\n".join(error.value.problems)


def test_valid_content_loads(tmp_path: Path) -> None:
    seed_dir = write_seed(tmp_path, {"friendship": [scenario_dict()]})

    data = load_seed(seed_dir)

    assert [(category, s.slug) for category, s in data.scenarios] == [
        ("friendship", "test-scenario")
    ]


def test_scenario_must_have_exactly_three_choices(tmp_path: Path) -> None:
    two = scenario_dict()["choices"][:2]

    assert "at least 3 items" in problems_for(tmp_path, scenario_dict(choices=two))


def test_four_choices_are_rejected(tmp_path: Path) -> None:
    four = [*scenario_dict()["choices"], {"text": "D", "weights": {"honesty": 1, "loyalty": 1}}]

    assert "at most 3 items" in problems_for(tmp_path, scenario_dict(choices=four))


def test_unknown_dimension_is_rejected(tmp_path: Path) -> None:
    choices = scenario_dict()["choices"]
    choices[0]["weights"] = {"bravery": 5, "loyalty": 2}

    assert "bravery" in problems_for(tmp_path, scenario_dict(choices=choices))


@pytest.mark.parametrize("bad_weight", [11, -1])
def test_weights_must_be_between_0_and_10(tmp_path: Path, bad_weight: int) -> None:
    choices = scenario_dict()["choices"]
    choices[0]["weights"]["honesty"] = bad_weight

    assert problems_for(tmp_path, scenario_dict(choices=choices))


def test_all_choices_must_weight_the_same_dimensions(tmp_path: Path) -> None:
    choices = scenario_dict()["choices"]
    choices[2]["weights"] = {"honesty": 5, "empathy": 5}

    assert "same set of dimensions" in problems_for(tmp_path, scenario_dict(choices=choices))


def test_a_dimension_that_never_varies_is_rejected(tmp_path: Path) -> None:
    choices = scenario_dict()["choices"]
    for choice in choices:
        choice["weights"]["loyalty"] = 5  # same on every choice: measures nothing

    assert "barely differs" in problems_for(tmp_path, scenario_dict(choices=choices))


def test_a_choice_needs_at_least_one_weight(tmp_path: Path) -> None:
    choices = scenario_dict()["choices"]
    for choice in choices:
        choice["weights"] = {}

    assert "between 1 and 4" in problems_for(tmp_path, scenario_dict(choices=choices))


def test_text_length_limits(tmp_path: Path) -> None:
    assert "at most 400" in problems_for(tmp_path, scenario_dict(situation="x" * 401))


@pytest.mark.parametrize("typo", ["dificulty", "titel"])
def test_misspelled_fields_are_rejected_not_ignored(tmp_path: Path, typo: str) -> None:
    assert "Extra inputs are not permitted" in problems_for(tmp_path, {**scenario_dict(), typo: 2})


def test_slug_must_be_lowercase_words(tmp_path: Path) -> None:
    assert problems_for(tmp_path, scenario_dict(slug="Not A Slug"))


def test_duplicate_slugs_across_files_are_rejected(tmp_path: Path) -> None:
    seed_dir = write_seed(
        tmp_path,
        {"friendship": [scenario_dict("same")], "money": [scenario_dict("same")]},
    )

    with pytest.raises(SeedValidationError) as error:
        load_seed(seed_dir)

    assert "already used" in "\n".join(error.value.problems)


def test_unknown_category_is_rejected(tmp_path: Path) -> None:
    seed_dir = write_seed(tmp_path, {"cooking": [scenario_dict()]})

    with pytest.raises(SeedValidationError) as error:
        load_seed(seed_dir)

    assert "unknown category 'cooking'" in "\n".join(error.value.problems)


def test_all_problems_are_reported_at_once(tmp_path: Path) -> None:
    seed_dir = write_seed(
        tmp_path,
        {
            "friendship": [scenario_dict("one", difficulty=9)],
            "money": [scenario_dict("two", title="")],
        },
    )

    with pytest.raises(SeedValidationError) as error:
        load_seed(seed_dir)

    assert len(error.value.problems) == 2
