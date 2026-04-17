"""SQLAlchemy engine, session factory, and FastAPI dependency."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Small pool — backend is single-process, low write volume.
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=2,
    max_overflow=2,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Session:
    """FastAPI dependency that yields a session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
