"""Database engine and session configuration.

Supports SQLite (local dev, default) and PostgreSQL (Vercel / production).
Set DATABASE_URL environment variable to switch:
  - SQLite (default): sqlite:///./bible.db   → stored at /app/bible.db in the container
  - PostgreSQL:       postgresql://user:pass@host/dbname  (Neon, Supabase, etc.)
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bible.db")

# Some providers (Heroku, Render, Neon) emit postgres:// which SQLAlchemy requires
# as postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    # SQLite needs check_same_thread=False when used with FastAPI's threading model
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't already exist (idempotent)."""
    # Import models so SQLAlchemy registers them with Base.metadata
    from app.models import db_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
