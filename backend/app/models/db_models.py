"""SQLAlchemy ORM table definitions.

Each "bible" gets its own table so they can evolve independently.
Currently:
  - custom_bible_entries  — user-defined timing bible overrides
Future:
  - tax_credit_bible      — tax credit rules per jurisdiction/code
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text, UniqueConstraint

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


class TaxCreditOverride(Base):
    """Per-project overrides for tax credit breakout bible values.

    Each row stores the override values for one account code within a named
    project. NULL means "use the bible default"; an explicit value overrides it.
    """

    __tablename__ = "tax_credit_overrides"
    __table_args__ = (UniqueConstraint("project_name", "account_code"),)

    id = Column(String(64), primary_key=True)  # "{project_name}::{account_code}"
    project_name = Column(String(200), nullable=False, index=True)
    account_code = Column(String(20), nullable=False)
    # FOR flag: None = currency-based formula, True = always FOR, False = never FOR
    is_foreign = Column(Boolean, nullable=True)
    # OUT flag: None = use bible default, True = force OUT, False = force not-OUT
    is_non_prov = Column(Boolean, nullable=True)
    fed_labour_pct = Column(Float, nullable=True)
    fed_svc_labour_pct = Column(Float, nullable=True)
    prov_labour_pct = Column(Float, nullable=True)
    prov_svc_labour_pct = Column(Float, nullable=True)
    svc_property_pct = Column(Float, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
