from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.category import Category
from app.db.models.choice import Choice
from app.db.models.enums import ScenarioSource, ScenarioStatus, enum_column


class Scenario(Base):
    __tablename__ = "scenarios"
    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 3", name="difficulty_range"),
        Index("ix_scenarios_category_status", "category_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stable human-readable key. The seed script upserts by slug, so re-running it is safe.
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(150))
    situation_text: Mapped[str] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    difficulty: Mapped[int] = mapped_column(default=1)
    status: Mapped[ScenarioStatus] = mapped_column(
        enum_column(ScenarioStatus, "status"), default=ScenarioStatus.DRAFT
    )
    source: Mapped[ScenarioSource] = mapped_column(
        enum_column(ScenarioSource, "source"), default=ScenarioSource.MANUAL
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    category: Mapped[Category] = relationship()
    choices: Mapped[list[Choice]] = relationship(
        order_by="Choice.position", cascade="all, delete-orphan"
    )
