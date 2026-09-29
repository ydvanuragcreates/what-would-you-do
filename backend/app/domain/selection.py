"""Choosing which scenarios go into a round. Pure logic: no database, easy to test.

Rules, in priority order:
1. Scenarios this player has never answered come first.
2. If there aren't enough of those, top up with the ones they saw longest ago.
3. When drawing from several categories (a "Random" round), spread evenly across
   them so a round isn't ten money dilemmas.
4. The final order is shuffled, so replayed scenarios aren't always at the end.
"""

import random
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import NamedTuple


class Candidate(NamedTuple):
    id: int
    category_id: int


def select_scenarios(
    candidates: Sequence[Candidate],
    last_seen: Mapping[int, datetime],
    count: int,
    rng: random.Random,
    *,
    spread_categories: bool,
) -> list[int]:
    """Return `count` distinct scenario ids in the order they should be asked.

    `last_seen` maps scenario id -> when this player last answered it. Scenarios
    missing from it count as never seen.
    """
    if count > len(candidates):
        raise ValueError(f"cannot pick {count} scenarios from {len(candidates)} candidates")

    unseen = [c for c in candidates if c.id not in last_seen]
    picked = _pick_unseen(unseen, count, rng, spread_categories)

    if len(picked) < count:
        seen = [c for c in candidates if c.id in last_seen]
        rng.shuffle(seen)  # random tie-break; the sort below is stable
        seen.sort(key=lambda c: last_seen[c.id])
        picked.extend(seen[: count - len(picked)])

    rng.shuffle(picked)
    return [c.id for c in picked]


def _pick_unseen(
    unseen: list[Candidate], count: int, rng: random.Random, spread_categories: bool
) -> list[Candidate]:
    if not spread_categories:
        pool = list(unseen)
        rng.shuffle(pool)
        return pool[:count]

    by_category: dict[int, list[Candidate]] = defaultdict(list)
    for candidate in unseen:
        by_category[candidate.category_id].append(candidate)
    queues = list(by_category.values())
    for queue in queues:
        rng.shuffle(queue)

    # Deal one from each category in turn (categories in a fresh random order each
    # pass, so no category always gets the first pick) until we have enough.
    picked: list[Candidate] = []
    while len(picked) < count and any(queues):
        rng.shuffle(queues)
        for queue in queues:
            if queue and len(picked) < count:
                picked.append(queue.pop())
    return picked
