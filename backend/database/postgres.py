from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create tables on startup.

    This is intentionally simple (no Alembic migrations) to satisfy the requirement that
    the Python backend creates all required tables in Postgres.
    """
    # Import models to ensure Base.metadata is populated.
    from backend.models.user import Base  # noqa: WPS433

    Base.metadata.create_all(bind=engine)


