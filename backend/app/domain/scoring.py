from collections.abc import Iterable

# Bump this whenever the maths or the profile rules change, so a stored result can
# always be traced to the rules that produced it.
SCORING_VERSION = 2

# A dimension seen only once is one data point, not a pattern. Showing "7.0" for it
# would look far more precise than it is, so it gets no score at all.
MIN_OBSERVATIONS = 2


def compute_scores(
    chosen_weights: Iterable[dict[str, int]], *, min_observations: int = MIN_OBSERVATIONS
) -> dict[str, float]:
    """Turn the weights of a round's chosen options into per-dimension scores (0-10).

    Each dimension's score is the average weight across the answers that measured
    it. A dimension measured fewer than `min_observations` times is left out: the
    result screen shows it as "not enough data this round".
    """
    answered = list(chosen_weights)
    if not answered:
        raise ValueError("cannot compute scores from zero answered questions")

    totals: dict[str, int] = {}
    counts: dict[str, int] = {}
    for weights in answered:
        for dimension, weight in weights.items():
            totals[dimension] = totals.get(dimension, 0) + weight
            counts[dimension] = counts.get(dimension, 0) + 1

    return {
        dimension: round(totals[dimension] / counts[dimension], 2)
        for dimension in totals
        if counts[dimension] >= min_observations
    }
