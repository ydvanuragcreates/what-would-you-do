"""What a player sees once a round is finished."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.crowd import CrowdStats
from app.schemas.scenario import ScenarioPublic


class ProfilePublic(BaseModel):
    key: str
    title: str
    summary: str


class DimensionScore(BaseModel):
    dimension: str  # machine key, e.g. "self_interest"
    label: str  # display name, e.g. "Self-interest"
    # 0-10. None means "not enough data this round": the dimension came up fewer
    # than twice, and one data point would look far more precise than it is.
    score: float | None


class QuestionReview(BaseModel):
    """One question of a finished round: what was asked, what you chose, what others chose."""

    question_number: int
    scenario: ScenarioPublic  # built via to_public, so it can't carry scoring weights
    your_choice_id: int
    crowd: CrowdStats  # other players only, never yourself


class RoundResultResponse(BaseModel):
    round_id: uuid.UUID
    category_id: int | None
    category_name: str  # "Random" when the round drew from every category
    completed_at: datetime
    profile: ProfilePublic
    scores: list[DimensionScore]  # always all 8 dimensions, in a fixed display order
    questions: list[QuestionReview]  # in the order they were asked
    disclaimer: str


class ResultSummary(BaseModel):
    round_id: uuid.UUID
    category_name: str
    completed_at: datetime
    profile: ProfilePublic


class ResultHistoryResponse(BaseModel):
    total: int
    results: list[ResultSummary]
