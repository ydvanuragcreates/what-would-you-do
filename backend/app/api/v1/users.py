from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.errors import ErrorResponse
from app.schemas.result import ResultHistoryResponse
from app.services import results as result_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me/results",
    response_model=ResultHistoryResponse,
    responses={401: {"model": ErrorResponse}},
)
def my_results(
    user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ResultHistoryResponse:
    """Your finished rounds, newest first."""
    return result_service.list_results(db, user_id=user.id, limit=limit, offset=offset)
