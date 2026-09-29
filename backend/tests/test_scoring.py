import pytest

from app.domain.scoring import compute_scores


def test_averages_each_dimension_independently() -> None:
    scores = compute_scores([{"honesty": 8, "loyalty": 4}, {"honesty": 2, "loyalty": 10}])

    assert scores == {"honesty": 5.0, "loyalty": 7.0}


def test_dimension_no_question_measured_is_absent() -> None:
    scores = compute_scores([{"honesty": 8}, {"honesty": 6}])

    assert "empathy" not in scores


def test_dimension_measured_only_once_is_left_out() -> None:
    """One data point isn't a pattern; a lone '2.0' would look far too precise."""
    scores = compute_scores([{"honesty": 8, "loyalty": 2}, {"honesty": 4}])

    assert scores == {"honesty": 6.0}


def test_a_round_where_nothing_repeats_has_no_scores() -> None:
    assert compute_scores([{"honesty": 8}, {"loyalty": 3}]) == {}


def test_minimum_observations_can_be_changed() -> None:
    scores = compute_scores([{"honesty": 8, "loyalty": 2}, {"honesty": 4}], min_observations=1)

    assert scores == {"honesty": 6.0, "loyalty": 2.0}


def test_rounds_to_two_decimal_places() -> None:
    scores = compute_scores([{"honesty": 1}, {"honesty": 1}, {"honesty": 2}])

    assert scores == {"honesty": 1.33}


def test_empty_input_raises() -> None:
    with pytest.raises(ValueError, match="zero answered questions"):
        compute_scores([])
