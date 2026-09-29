"""Guards for the real content in backend/seed/. These run on every `pytest`, so a typo in
a YAML file is caught here, not when someone plays. No database needed."""

from collections import Counter

import pytest

from app.domain.dimensions import Dimension
from app.services.seeding import SeedData, load_seed
from scripts.seed import DEFAULT_SEED_DIR


@pytest.fixture(scope="module")
def seed() -> SeedData:
    return load_seed(DEFAULT_SEED_DIR)


def test_real_seed_files_are_valid(seed: SeedData) -> None:
    assert len(seed.categories) == 8
    assert len(seed.scenarios) >= 24


def test_every_category_has_scenarios(seed: SeedData) -> None:
    per_category = Counter(category for category, _ in seed.scenarios)

    for category in seed.categories:
        assert per_category[category.slug] >= 3, f"'{category.slug}' needs more scenarios"


def test_every_dimension_is_measured_often_enough(seed: SeedData) -> None:
    """If a dimension is rarely measured, its score in a 10-question round is noise."""
    measured: Counter[Dimension] = Counter()
    for _, scenario in seed.scenarios:
        measured.update(scenario.choices[0].weights.keys())

    for dimension in Dimension:
        assert measured[dimension] >= 3, f"'{dimension.value}' is measured by too few scenarios"
