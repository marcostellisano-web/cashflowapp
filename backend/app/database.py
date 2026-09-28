"""Database engine and session configuration.

Supports SQLite (local dev, default) and PostgreSQL (Vercel / production).
Set DATABASE_URL environment variable to switch:
  - SQLite (default): sqlite:///./bible.db   → stored at /app/bible.db in the container
  - PostgreSQL:       postgresql://user:pass@host/dbname  (Neon, Supabase, etc.)
"""

import os
from threading import Lock

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

def _default_database_url() -> str:
    """Return a writable SQLite location for the current runtime.

    Vercel's deployed source directory is read-only.  Without a configured
    production database, using ``./bible.db`` there prevents the FastAPI app
    from starting, which makes even database-free routes such as budget upload
    return a generic server error.  ``/tmp`` is Vercel's writable fallback.
    """
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/cashflowapp-bible.db"
    return "sqlite:///./bible.db"


def _normalize_database_url(url: str) -> str:
    """Select the installed psycopg2 driver for provider PostgreSQL URLs."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


DATABASE_URL = _normalize_database_url(
    os.getenv("DATABASE_URL") or _default_database_url()
)

_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    # SQLite: allow cross-thread usage (FastAPI runs handlers in threads)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
else:
    # PostgreSQL on Vercel serverless: NullPool creates a fresh connection per
    # request and closes it immediately, preventing connection exhaustion on
    # platforms where processes don't persist between invocations.
    engine = create_engine(DATABASE_URL, poolclass=NullPool)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
_initialization_lock = Lock()
_initialized = False


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    ensure_db_initialized()
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
    _migrate()


def ensure_db_initialized() -> None:
    """Initialize storage on first use by an endpoint that needs it.

    Keeping this out of application startup allows database-free routes such
    as budget upload and health checks to remain available when a production
    database is temporarily unreachable or misconfigured.
    """
    global _initialized
    if _initialized:
        return
    with _initialization_lock:
        if not _initialized:
            init_db()
            _initialized = True


def _migrate() -> None:
    """Apply incremental schema changes that create_all cannot handle.

    Safe to run on every startup — each statement is idempotent.
    """
    with engine.connect() as conn:
        if _is_sqlite:
            # SQLite ADD COLUMN IF NOT EXISTS requires 3.37+; use try/except
            try:
                conn.execute(text(
                    "ALTER TABLE breakout_bible_entries "
                    "ADD COLUMN description TEXT NOT NULL DEFAULT ''"
                ))
                conn.commit()
            except Exception:
                pass  # column already exists
        else:
            conn.execute(text(
                "ALTER TABLE breakout_bible_entries "
                "ADD COLUMN IF NOT EXISTS description TEXT NOT NULL DEFAULT ''"
            ))
            conn.commit()
