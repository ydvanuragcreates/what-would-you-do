"""Anonymous crowd statistics: how did OTHER players answer a scenario?

Counting rules (each one protects the numbers or the players):
- only answers from COMPLETED rounds, so abandoned or in-progress rounds add no noise;
- only each player's FIRST such answer per scenario, so replaying can't skew the split;
- never the requesting player's own answers, so "others" really means others;
- below `min_sample` responses nothing is revealed, not even the count.
"""

import uuid
from collections.abc import Mapping, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Round, Scenario, UserAnswer
from app.db.models.enums import RoundStatus
from app.schemas.crowd import ChoiceShare, CrowdStats
from app.services.scenarios import LABELS

NOT_ENOUGH_RESPONSES = "Not enough responses yet."


def largest_remainder_percentages(counts: Mapping[int, int]) -> dict[int, int]:
    """Whole percentages that add up to exactly 100.

    Plain rounding can give 33 + 33 + 33 = 99. Instead, everyone gets the rounded-down
    share and the leftover points go to whoever lost the most in rounding (ties: lower id).
    """
    total = sum(counts.values())
    if total == 0:
        return dict.fromkeys(counts, 0)

    exact = {key: count * 100 / total for key, count in counts.items()}
    shares = {key: int(value) for key, value in exact.items()}
    by_lost_fraction = sorted(exact, key=lambda key: (-(exact[key] - shares[key]), key))
    for key in by_lost_fraction[: 100 - sum(shares.values())]:
        shares[key] += 1
    return shares


def crowd_stats_for(
    db: Session,
    scenarios: Sequence[Scenario],
    *,
    exclude_user_id: uuid.UUID,
    min_sample: int | None = None,
) -> dict[int, CrowdStats]:
    """Crowd statistics for several scenarios at once (one query), keyed by scenario id.

    Each scenario must have its `choices` loaded.
    """
    if not scenarios:
        return {}
    threshold = min_sample if min_sample is not None else get_settings().min_stats_sample
    counts = _first_answer_counts(db, [s.id for s in scenarios], exclude_user_id)

    return {scenario.id: _stats_for_scenario(scenario, counts, threshold) for scenario in scenarios}


def _stats_for_scenario(
    scenario: Scenario, counts: Mapping[tuple[int, int], int], threshold: int
) -> CrowdStats:
    per_choice = {c.id: counts.get((scenario.id, c.id), 0) for c in scenario.choices}
    total = sum(per_choice.values())
    if total < threshold:
        return CrowdStats(
            available=False, total_responses=None, choices=[], message=NOT_ENOUGH_RESPONSES
        )

    percent = largest_remainder_percentages(per_choice)
    return CrowdStats(
        available=True,
        total_responses=total,
        choices=[
            ChoiceShare(choice_id=c.id, label=LABELS[c.position], percent=percent[c.id])
            for c in scenario.choices
        ],
        message=None,
    )


def _first_answer_counts(
    db: Session, scenario_ids: Sequence[int], exclude_user_id: uuid.UUID
) -> dict[tuple[int, int], int]:
    """{(scenario_id, choice_id): number of players whose first counted answer was that choice}."""
    first_answers = (
        select(UserAnswer.scenario_id, UserAnswer.choice_id)
        .join(Round, Round.id == UserAnswer.round_id)
        .where(
            Round.status == RoundStatus.COMPLETED,
            Round.user_id != exclude_user_id,
            UserAnswer.scenario_id.in_(scenario_ids),
        )
        # PostgreSQL "DISTINCT ON": keep one row per (player, scenario), the earliest.
        .distinct(Round.user_id, UserAnswer.scenario_id)
        .order_by(Round.user_id, UserAnswer.scenario_id, UserAnswer.answered_at, UserAnswer.id)
        .subquery()
    )
    rows = db.execute(
        select(first_answers.c.scenario_id, first_answers.c.choice_id, func.count()).group_by(
            first_answers.c.scenario_id, first_answers.c.choice_id
        )
    ).tuples()
    return {(scenario_id, choice_id): count for scenario_id, choice_id, count in rows}
