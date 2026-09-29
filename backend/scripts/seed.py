"""Load scenarios from backend/seed/ into the database.

    uv run python -m scripts.seed --check    # validate the YAML files only, no database
    uv run python -m scripts.seed            # validate, then create/update in the database

Safe to run as often as you like: scenarios are matched by slug, nothing is ever deleted,
and scenarios players have already answered can't have their text or choices changed.
"""

import argparse
import sys
from pathlib import Path

from app.db.session import SessionLocal, engine
from app.services.seeding import SeedValidationError, apply_seed, load_seed

DEFAULT_SEED_DIR = Path(__file__).resolve().parent.parent / "seed"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed categories and scenarios.")
    parser.add_argument(
        "--check", action="store_true", help="validate the files, don't touch the database"
    )
    parser.add_argument("--seed-dir", type=Path, default=DEFAULT_SEED_DIR)
    args = parser.parse_args(argv)

    try:
        data = load_seed(args.seed_dir)
    except SeedValidationError as error:
        print(f"Seed files have {len(error.problems)} problem(s):")
        for problem in error.problems:
            print(f"  - {problem}")
        return 1
    print(f"Seed files OK: {len(data.categories)} categories, {len(data.scenarios)} scenarios.")
    if args.check:
        return 0

    print(f"Writing to database '{engine.url.database}' ...")
    with SessionLocal() as db:
        report = apply_seed(db, data)

    print(f"  created:   {len(report.created)}")
    print(f"  updated:   {len(report.updated)}")
    print(f"  unchanged: {report.unchanged}")
    if report.blocked:
        print(f"  BLOCKED:   {len(report.blocked)} (players already answered these)")
        for slug in report.blocked:
            print(f"    - {slug}: text/choices differ from the database. To change a scenario that")
            print("      has answers, set the old one to `status: retired` and add a new slug.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
