import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.errors import ErrorResponse
from app.schemas.result import RoundResultResponse
from app.services import results as result_service

router = APIRouter(prefix="/results", tags=["results"])


@router.get(
    "/{round_id}",
    response_model=RoundResultResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def get_result(round_id: uuid.UUID, user: CurrentUser, db: DbSession) -> RoundResultResponse:
    """The decision profile and scores for one of your finished rounds."""
    return result_service.get_result(db, round_id=round_id, user_id=user.id)
