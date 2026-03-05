"""SQLAlchemy ORM table definitions.

Each "bible" gets its own table so they can evolve independently.
Currently:
  - custom_bible_entries  — user-defined timing bible overrides
Future:
  - tax_credit_bible      — tax credit rules per jurisdiction/code
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text

from app.database import Base


class CustomBibleEntry(Base):
    """User-defined code → timing-pattern mapping stored server-side."""

    __tablename__ = "custom_bible_entries"

    account_code = Column(String(20), primary_key=True)
    description = Column(Text, nullable=False, default="")
    timing_pattern = Column(String(100), nullable=False)
    timing_title = Column(String(200), nullable=False)
    timing_details = Column(Text, nullable=False, default="")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
