"""The decision-profile rules. Pure logic: no database."""

import pytest

from app.domain.dimensions import Dimension
from app.domain.profiles import (
    ALL_PROFILES,
    BALANCED,
    DISCLAIMER,
    pick_profile,
    profile_for,
)


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        # tier 1: combinations
        ({"loyalty": 8, "responsibility": 6}, "loyal-realist"),
        ({"empathy": 7, "fairness": 6}, "empathetic-negotiator"),
        ({"self_interest": 8, "risk": 3}, "strategic-thinker"),
        ({"social_pressure": 2}, "independent-mind"),
        # tier 2: strongest trait
        ({"honesty": 9, "loyalty": 4}, "straight-shooter"),
        ({"loyalty": 8}, "devoted-ally"),
        ({"empathy": 8}, "open-heart"),
        ({"self_interest": 8, "risk": 7}, "pragmatist"),  # too risky to be 'strategic'
        ({"risk": 9}, "risk-taker"),
        ({"responsibility": 8}, "dutiful-guardian"),
        ({"fairness": 8}, "fair-minded-judge"),
        ({"social_pressure": 9}, "harmony-keeper"),
        # tier 3
        ({"honesty": 5, "loyalty": 5.5, "empathy": 4}, "balanced-decision-maker"),
        ({}, "balanced-decision-maker"),
    ],
)
def test_profile_for_typical_scores(scores: dict[str, float], expected: str) -> None:
    assert pick_profile(scores).key == expected


def test_combination_beats_single_trait() -> None:
    # Loyalty is the top trait, but loyalty + responsibility is the more specific story.
    assert pick_profile({"loyalty": 9, "responsibility": 5.5}).key == "loyal-realist"


def test_earlier_combination_wins_when_several_match() -> None:
    scores = {"loyalty": 8, "responsibility": 6, "social_pressure": 2}

    assert pick_profile(scores).key == "loyal-realist"  # not independent-mind


def test_unmeasured_dimension_never_satisfies_a_rule() -> None:
    # "Strategic thinker" needs a LOW risk score; no risk data must not count as low risk.
    assert pick_profile({"self_interest": 8}).key == "pragmatist"


def test_thresholds_are_inclusive() -> None:
    assert pick_profile({"honesty": 6.5}).key == "straight-shooter"
    assert pick_profile({"honesty": 6.49}).key == "balanced-decision-maker"


def test_equal_top_traits_break_ties_alphabetically() -> None:
    assert pick_profile({"loyalty": 8, "honesty": 8}).key == "straight-shooter"


def test_same_scores_always_give_the_same_profile() -> None:
    scores = {"loyalty": 7.2, "honesty": 6.9, "risk": 4.0}

    assert {pick_profile(scores).key for _ in range(50)} == {pick_profile(scores).key}


def test_every_dimension_can_produce_a_profile() -> None:
    """A strong score in any single dimension must never fall through to 'balanced'
    unless a combination rule takes it first."""
    for dimension in Dimension:
        if dimension is Dimension.SOCIAL_PRESSURE:
            continue  # low social pressure is handled by 'independent-mind'; high covered below
        assert pick_profile({dimension.value: 9.0}) != BALANCED, dimension


def test_unknown_dimensions_in_old_data_are_ignored() -> None:
    assert pick_profile({"bravery": 9.0}).key == "balanced-decision-maker"


def test_stored_key_from_older_rules_is_rederived_from_scores() -> None:
    profile = profile_for("loyalty", {"loyalty": 8})  # v1 stored the raw dimension name

    assert profile.key == "devoted-ally"


def test_stored_current_key_is_returned_as_is() -> None:
    assert profile_for("risk-taker", {"honesty": 9}).key == "risk-taker"


def test_profile_keys_are_unique_and_complete() -> None:
    keys = [profile.key for profile in ALL_PROFILES]

    assert len(keys) == len(set(keys)) == 13


def test_profile_wording_describes_the_round_not_the_person() -> None:
    """Entertainment, not judgement: 'in this round', never 'you are'."""
    for profile in ALL_PROFILES:
        summary = profile.summary.lower()
        assert "in this round" in summary, profile.key
        assert "you are" not in summary and "you're" not in summary, profile.key
        assert profile.title.startswith("The "), profile.key


def test_disclaimer_says_it_is_not_an_assessment() -> None:
    assert "not a psychological or moral assessment" in DISCLAIMER
