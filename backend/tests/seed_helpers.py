"""Build small seed directories for tests."""

from pathlib import Path
from typing import Any

import yaml


def scenario_dict(slug: str = "test-scenario", **overrides: Any) -> dict[str, Any]:
    """A valid scenario as it would appear in YAML."""
    scenario: dict[str, Any] = {
        "slug": slug,
        "title": "A test scenario",
        "difficulty": 2,
        "situation": "Something happens and you must decide what to do.",
        "choices": [
            {"text": "Option A", "weights": {"honesty": 9, "loyalty": 2}},
            {"text": "Option B", "weights": {"honesty": 2, "loyalty": 9}},
            {"text": "Option C", "weights": {"honesty": 5, "loyalty": 5}},
        ],
    }
    scenario.update(overrides)
    return scenario


def write_seed(
    root: Path,
    files: dict[str, list[dict[str, Any]]],
    categories: tuple[str, ...] = ("friendship", "money"),
) -> Path:
    """Write `files` ({category slug: [scenario dicts]}) as a seed directory and return it."""
    (root / "scenarios").mkdir(parents=True, exist_ok=True)
    cats = [
        {"slug": slug, "name": slug.title(), "emoji": "", "sort_order": i}
        for i, slug in enumerate(categories, start=1)
    ]
    (root / "categories.yaml").write_text(yaml.safe_dump(cats), encoding="utf-8")
    for category, scenarios in files.items():
        content = {"category": category, "scenarios": scenarios}
        (root / "scenarios" / f"{category}.yaml").write_text(
            yaml.safe_dump(content), encoding="utf-8"
        )
    return root
