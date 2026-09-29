"""What players are allowed to see of a round. `question` is always built via
`scenario_service.to_public`, so `Choice.weights` can never leak through here.
`result` is only ever populated once the round is COMPLETED.
"""

import uuid

from pydantic import BaseModel, ConfigDict

from app.db.models.enums import RoundStatus
from app.schemas.crowd import CrowdStats
from app.schemas.scenario import ScenarioPublic


class StartRoundRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: int | None = None


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: int
    choice_id: int


class RoundResultPublic(BaseModel):
    scores: dict[str, float]
    profile_key: str


class LastAnswer(BaseModel):
    """The reveal shown right after answering: what you picked, and what others picked."""

    scenario_id: int
    your_choice_id: int
    crowd: CrowdStats


class RoundStateResponse(BaseModel):
    id: uuid.UUID
    status: RoundStatus
    category_id: int | None
    question_count: int
    current_question_number: int | None  # 1-based; None once not IN_PROGRESS
    question: ScenarioPublic | None  # None once not IN_PROGRESS
    result: RoundResultPublic | None  # None until COMPLETED
    # Only set on the response to POST .../answers, and only for the question just answered.
    last_answer: LastAnswer | None = None
