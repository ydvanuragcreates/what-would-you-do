from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

# pool_pre_ping: free-tier databases (Neon) close idle connections; this checks a
# connection is alive before using it instead of failing the user's request.
# pool_recycle: drop connections older than 5 minutes for the same reason.
# connect_timeout: without it an unreachable database blocks a request (and the
# health check) for as long as the OS allows. 10s still covers a Neon cold start.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=300,
    connect_args={"connect_timeout": 10},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
