"""Anonymous "how did other players answer" statistics.

Only aggregate numbers live here: there is no user id, username or per-person field
anywhere in these models, so an individual can't be identified through them.
"""

from typing import Literal

from pydantic import BaseModel


class ChoiceShare(BaseModel):
    choice_id: int
    label: Literal["A", "B", "C"]
    percent: int  # whole percent; the three shares always add up to exactly 100


class CrowdStats(BaseModel):
    # False until enough other players have answered. Nothing is estimated or made up.
    available: bool
    total_responses: int | None  # None while unavailable: even a tiny count can be revealing
    choices: list[ChoiceShare]  # empty while unavailable
    message: str | None  # "Not enough responses yet." while unavailable
