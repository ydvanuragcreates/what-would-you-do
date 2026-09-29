import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.schemas.errors import ErrorResponse
from app.schemas.round import AnswerRequest, RoundStateResponse, StartRoundRequest
from app.services import rounds as round_service

router = APIRouter(prefix="/rounds", tags=["rounds"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RoundStateResponse,
    responses={401: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def start_round(body: StartRoundRequest, user: CurrentUser, db: DbSession) -> RoundStateResponse:
    """Start a round. `category_id=null` means Random: every category."""
    return round_service.start_round(
        db,
        user_id=user.id,
        category_id=body.category_id,
        round_length=get_settings().round_length,
    )


@router.get(
    "/{round_id}",
    response_model=RoundStateResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_round(round_id: uuid.UUID, user: CurrentUser, db: DbSession) -> RoundStateResponse:
    return round_service.get_round_state(db, round_id=round_id, user_id=user.id)


@router.post(
    "/{round_id}/answers",
    response_model=RoundStateResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def submit_answer(
    round_id: uuid.UUID, body: AnswerRequest, user: CurrentUser, db: DbSession
) -> RoundStateResponse:
    """Answer the round's current question. `scenario_id` must match that current
    question; answering out of order or a question already answered is a 409."""
    return round_service.submit_answer(
        db,
        round_id=round_id,
        user_id=user.id,
        scenario_id=body.scenario_id,
        choice_id=body.choice_id,
    )
