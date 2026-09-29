"""Turning a round's scores into a playful "decision style". Deterministic and rule-based:
the same scores always give the same profile, and no AI model is involved.

Three tiers, checked in order:
1. Combination profiles, e.g. "The Loyal Realist" (high loyalty AND some responsibility).
2. A "leaning" profile named after the strongest trait, if that trait is strong enough.
3. "The Balanced Decision Maker" when nothing stands out.

Wording rule: these describe the ROUND, never the person. Summaries say "your
decisions in this round resembled/leaned toward...", never "you are...". This is
entertainment and self-reflection, not an assessment.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from app.domain.dimensions import Dimension

DISCLAIMER = (
    "Just for fun and self-reflection. This is not a psychological or moral assessment, "
    "and it only reflects the choices you made in this one round."
)

# Scores run 0-10 and typically cluster around 5, so ~6.5 means "clearly leaned this way".
HIGH = 6.5
LOW = 3.5


@dataclass(frozen=True)
class Profile:
    key: str
    title: str
    summary: str


@dataclass(frozen=True)
class Condition:
    """`dimension` must score at least `at_least` and/or at most `at_most`.
    A dimension that wasn't measured this round never satisfies a condition."""

    dimension: Dimension
    at_least: float | None = None
    at_most: float | None = None

    def holds(self, scores: Mapping[str, float]) -> bool:
        value = scores.get(self.dimension.value)
        if value is None:
            return False
        if self.at_least is not None and value < self.at_least:
            return False
        return not (self.at_most is not None and value > self.at_most)


LOYAL_REALIST = Profile(
    "loyal-realist",
    "The Loyal Realist",
    "Your decisions in this round resembled someone who puts the people close to them "
    "first, while still weighing the consequences.",
)
EMPATHETIC_NEGOTIATOR = Profile(
    "empathetic-negotiator",
    "The Empathetic Negotiator",
    "Your decisions in this round leaned toward understanding how everyone felt and "
    "looking for a fair middle ground.",
)
STRATEGIC_THINKER = Profile(
    "strategic-thinker",
    "The Strategic Thinker",
    "Your decisions in this round leaned toward protecting your own position and "
    "avoiding unnecessary gambles.",
)
INDEPENDENT_MIND = Profile(
    "independent-mind",
    "The Independent Mind",
    "Your choices in this round held steady even when the group might have pulled the other way.",
)

# Tier 1: (profile, all of these conditions must hold). Earlier rules win.
COMBINATION_RULES: tuple[tuple[Profile, tuple[Condition, ...]], ...] = (
    (
        LOYAL_REALIST,
        (
            Condition(Dimension.LOYALTY, at_least=HIGH),
            Condition(Dimension.RESPONSIBILITY, at_least=5),
        ),
    ),
    (
        EMPATHETIC_NEGOTIATOR,
        (Condition(Dimension.EMPATHY, at_least=HIGH), Condition(Dimension.FAIRNESS, at_least=5.5)),
    ),
    (
        STRATEGIC_THINKER,
        (Condition(Dimension.SELF_INTEREST, at_least=HIGH), Condition(Dimension.RISK, at_most=4.5)),
    ),
    (INDEPENDENT_MIND, (Condition(Dimension.SOCIAL_PRESSURE, at_most=LOW),)),
)

# Tier 2: one profile per dimension, used when it's the strongest trait and >= HIGH.
LEANING_PROFILES: dict[Dimension, Profile] = {
    Dimension.HONESTY: Profile(
        "straight-shooter",
        "The Straight Shooter",
        "Your decisions in this round leaned toward telling it like it is, even when "
        "the truth was uncomfortable.",
    ),
    Dimension.LOYALTY: Profile(
        "devoted-ally",
        "The Devoted Ally",
        "Your decisions in this round leaned toward standing by the people you care about.",
    ),
    Dimension.EMPATHY: Profile(
        "open-heart",
        "The Open Heart",
        "Your decisions in this round leaned toward putting other people's feelings first.",
    ),
    Dimension.SELF_INTEREST: Profile(
        "pragmatist",
        "The Pragmatist",
        "Your decisions in this round leaned toward looking out for your own interests.",
    ),
    Dimension.RISK: Profile(
        "risk-taker",
        "The Risk Taker",
        "Your decisions in this round leaned toward taking the chance and seeing what happens.",
    ),
    Dimension.RESPONSIBILITY: Profile(
        "dutiful-guardian",
        "The Dutiful Guardian",
        "Your decisions in this round leaned toward doing what needs doing, even when "
        "it was inconvenient.",
    ),
    Dimension.FAIRNESS: Profile(
        "fair-minded-judge",
        "The Fair-Minded Judge",
        "Your decisions in this round leaned toward making sure everyone got a fair deal.",
    ),
    Dimension.SOCIAL_PRESSURE: Profile(
        "harmony-keeper",
        "The Harmony Keeper",
        "Your decisions in this round leaned toward keeping the peace and going along "
        "with the group.",
    ),
}

BALANCED = Profile(
    "balanced-decision-maker",
    "The Balanced Decision Maker",
    "Your decisions in this round didn't lean strongly in any one direction. You "
    "weighed each situation on its own terms.",
)

ALL_PROFILES: tuple[Profile, ...] = (
    *(profile for profile, _ in COMBINATION_RULES),
    *LEANING_PROFILES.values(),
    BALANCED,
)
_BY_KEY = {profile.key: profile for profile in ALL_PROFILES}
_LEANING_BY_DIMENSION_KEY = {dim.value: profile for dim, profile in LEANING_PROFILES.items()}


def pick_profile(scores: Mapping[str, float]) -> Profile:
    for profile, conditions in COMBINATION_RULES:
        if all(condition.holds(scores) for condition in conditions):
            return profile

    known = {dim: value for dim, value in scores.items() if dim in _LEANING_BY_DIMENSION_KEY}
    if known:
        strongest = min(known, key=lambda dim: (-known[dim], dim))  # ties: alphabetical
        if known[strongest] >= HIGH:
            return _LEANING_BY_DIMENSION_KEY[strongest]
    return BALANCED


def profile_for(key: str, scores: Mapping[str, float]) -> Profile:
    """The profile stored on a result. Results saved under older rules may carry a key
    that no longer exists; those are re-derived from their scores instead of failing."""
    return _BY_KEY.get(key) or pick_profile(scores)
