import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import RoundStatus, enum_column
from app.db.models.round_question import RoundQuestion
from app.db.models.round_result import RoundResult
from app.db.models.user_answer import UserAnswer


class Round(Base):
    __tablename__ = "rounds"
    __table_args__ = (
        CheckConstraint("question_count > 0", name="question_count_positive"),
        Index("ix_rounds_user_id_started_at", "user_id", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # NULL means "Random" (questions drawn from every category).
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    status: Mapped[RoundStatus] = mapped_column(
        enum_column(RoundStatus, "status"), default=RoundStatus.IN_PROGRESS
    )
    question_count: Mapped[int]
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None]

    questions: Mapped[list[RoundQuestion]] = relationship(
        order_by="RoundQuestion.question_order", cascade="all, delete-orphan"
    )
    answers: Mapped[list[UserAnswer]] = relationship(cascade="all, delete-orphan")
    result: Mapped[RoundResult | None] = relationship(cascade="all, delete-orphan")
