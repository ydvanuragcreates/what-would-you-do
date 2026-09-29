from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Choice(Base):
    __tablename__ = "choices"
    __table_args__ = (
        CheckConstraint("position BETWEEN 1 AND 3", name="position_range"),
        # A scenario has at most one choice per slot (A=1, B=2, C=3).
        UniqueConstraint("scenario_id", "position", name="uq_choices_scenario_id_position"),
        # Looks redundant (id is already unique) but it is the target that lets
        # user_answers use a composite foreign key (choice_id, scenario_id), which
        # guarantees an answer's choice belongs to the answer's scenario.
        UniqueConstraint("id", "scenario_id", name="uq_choices_id_scenario_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"))
    position: Mapped[int]
    choice_text: Mapped[str] = mapped_column(String(300))
    # Hidden scoring metadata, e.g. {"honesty": 8, "loyalty": 3}. Sparse on purpose:
    # only the dimensions this choice actually says something about.
    # NEVER return this column from a public API schema.
    weights: Mapped[dict[str, int]]
