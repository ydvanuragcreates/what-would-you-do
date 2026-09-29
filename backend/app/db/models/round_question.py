import uuid

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RoundQuestion(Base):
    """Which scenarios a round contains, and in what order (fixed when the round starts)."""

    __tablename__ = "round_questions"
    __table_args__ = (
        CheckConstraint("question_order >= 1", name="question_order_positive"),
        UniqueConstraint("round_id", "question_order", name="uq_round_questions_round_id_order"),
        # No duplicate scenarios within a round. Also the target of user_answers'
        # composite foreign key (round_id, scenario_id).
        UniqueConstraint("round_id", "scenario_id", name="uq_round_questions_round_id_scenario_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    round_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rounds.id", ondelete="CASCADE"))
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id"))
    question_order: Mapped[int]
