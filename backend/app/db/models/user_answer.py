import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, ForeignKeyConstraint, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserAnswer(Base):
    __tablename__ = "user_answers"
    __table_args__ = (
        # One answer per question per round. This is what makes duplicate-answer
        # prevention safe even if two requests race each other.
        UniqueConstraint("round_id", "scenario_id", name="uq_user_answers_round_id_scenario_id"),
        # The scenario must actually be part of this round...
        ForeignKeyConstraint(
            ["round_id", "scenario_id"],
            ["round_questions.round_id", "round_questions.scenario_id"],
            name="fk_user_answers_round_question",
            ondelete="CASCADE",
        ),
        # ...and the chosen option must belong to that same scenario.
        ForeignKeyConstraint(
            ["choice_id", "scenario_id"],
            ["choices.id", "choices.scenario_id"],
            name="fk_user_answers_choice_in_scenario",
        ),
        # Speeds up the "how did everyone answer this scenario" aggregation.
        Index("ix_user_answers_scenario_id_choice_id", "scenario_id", "choice_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    round_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rounds.id", ondelete="CASCADE"))
    scenario_id: Mapped[int]
    choice_id: Mapped[int]
    answered_at: Mapped[datetime] = mapped_column(server_default=func.now())
