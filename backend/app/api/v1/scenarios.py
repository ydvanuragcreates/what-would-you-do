from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_current_user
from app.core.config import get_settings
from app.schemas.errors import ErrorResponse
from app.schemas.scenario import CategoriesResponse
from app.services import scenarios as scenario_service

# There is deliberately no "list all scenarios" endpoint: players only ever see
# scenarios inside their own rounds, so the question bank can't be scraped.
router = APIRouter(
    prefix="/scenarios",
    tags=["scenarios"],
    dependencies=[Depends(get_current_user)],  # login required
)


@router.get(
    "/categories",
    response_model=CategoriesResponse,
    responses={401: {"model": ErrorResponse}},
)
def list_categories(db: DbSession) -> CategoriesResponse:
    """Categories for the picker, with how many scenarios each has and whether
    it can fill a whole round yet. `random` covers the "Random" option."""
    return scenario_service.list_categories(db, round_length=get_settings().round_length)
