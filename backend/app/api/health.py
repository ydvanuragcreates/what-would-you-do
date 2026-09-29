import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
def liveness() -> HealthResponse:
    """Is the process up? Deliberately does NOT touch the database, so a sleeping
    free-tier database can't make the hosting platform think the app is dead."""
    return HealthResponse(status="ok")


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse}},
)
def readiness(db: DbSession, response: Response) -> HealthResponse:
    """Can we actually serve traffic? Checks the database connection."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Readiness check failed: database unreachable")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="unavailable", database="down")
    return HealthResponse(status="ok", database="up")
