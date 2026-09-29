from datetime import datetime

from sqlalchemy import DateTime, MetaData
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase

# Explicit constraint names. Without this, Postgres invents names and Alembic
# can't reliably drop or alter constraints in later migrations.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    # Lets us write `Mapped[datetime]` / `Mapped[dict[str, int]]` in models
    # and get timezone-aware timestamps / JSONB columns automatically.
    type_annotation_map = {
        datetime: DateTime(timezone=True),
        dict[str, int]: JSONB,
        dict[str, float]: JSONB,
    }
