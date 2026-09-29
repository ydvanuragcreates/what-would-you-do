from enum import StrEnum

from sqlalchemy import Enum


class ScenarioStatus(StrEnum):
    DRAFT = "draft"  # AI- or human-written, not yet reviewed; never shown to players
    ACTIVE = "active"
    RETIRED = "retired"  # kept forever so old answers still make sense


class ScenarioSource(StrEnum):
    MANUAL = "manual"
    AI = "ai"


class RoundStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


def enum_column(enum_cls: type[StrEnum], name: str) -> Enum:
    """Store a StrEnum as VARCHAR + CHECK constraint (not a native Postgres ENUM).

    Native ENUMs are painful to change with Alembic; a CHECK constraint is easy.
    We store the lowercase value ("in_progress"), not the Python member name.
    """
    return Enum(
        enum_cls,
        native_enum=False,
        length=20,
        values_callable=lambda members: [m.value for m in members],
        create_constraint=True,
        name=name,
    )
