"""Import every model here so `Base.metadata` knows about all tables (Alembic relies on this)."""

from app.db.models.category import Category
from app.db.models.choice import Choice
from app.db.models.round import Round
from app.db.models.round_question import RoundQuestion
from app.db.models.round_result import RoundResult
from app.db.models.scenario import Scenario
from app.db.models.user import User
from app.db.models.user_answer import UserAnswer

__all__ = [
    "Category",
    "Choice",
    "Round",
    "RoundQuestion",
    "RoundResult",
    "Scenario",
    "User",
    "UserAnswer",
]
