import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RoundResult(Base):
    __tablename__ = "round_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rounds.id", ondelete="CASCADE"), unique=True
    )
    # Dimension -> 0..10 score, e.g. {"honesty": 7.4, "loyalty": 8.6}. A dimension
    # with too little signal is simply absent. JSONB so adding a dimension needs no migration.
    scores: Mapped[dict[str, float]]
    profile_key: Mapped[str] = mapped_column(String(50))
    # Which version of the scoring rules produced this row, so old results stay explainable.
    scoring_version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
