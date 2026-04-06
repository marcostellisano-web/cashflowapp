"""SQLAlchemy ORM table definitions.

Each "bible" gets its own table so they can evolve independently.
  - custom_bible_entries   — user-defined timing bible overrides
  - breakout_bible_entries — global tax credit breakout bible customisations
  - tax_credit_overrides   — per-project tax credit overrides
  - bible_presets          — named uploaded bible versions
  - bible_preset_entries   — entries belonging to a named bible preset
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint

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


class BreakoutBibleEntry(Base):
    """Global (non-project-specific) customisations to the tax credit breakout bible.

    Standard BREAKOUT_BIBLE entries are stored here when their values are
    overridden. Entirely new (non-standard) account codes can also be added.
    Absent rows fall back to the Python defaults automatically.
    """

    __tablename__ = "breakout_bible_entries"

    account_code        = Column(String(20), primary_key=True)
    description         = Column(Text,    nullable=False, default="")
    is_non_prov         = Column(Boolean, nullable=False, default=False)
    prov_labour_pct     = Column(Float,   nullable=False, default=0.0)
    fed_labour_pct      = Column(Float,   nullable=False, default=0.0)
    prov_svc_labour_pct = Column(Float,   nullable=False, default=0.0)
    svc_property_pct    = Column(Float,   nullable=False, default=0.0)
    fed_svc_labour_pct  = Column(Float,   nullable=False, default=0.0)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class BiblePreset(Base):
    """A named, uploadable version of the breakout bible.

    One preset can be marked is_active=True at a time; when active its entries
    serve as the base bible for tax-credit generation (overriding the hardcoded
    BREAKOUT_BIBLE defaults, but themselves overrideable by breakout_bible_entries).
    """

    __tablename__ = "bible_presets"

    id         = Column(Integer,              primary_key=True, autoincrement=True)
    name       = Column(String(200),          nullable=False)
    is_active  = Column(Boolean,              nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class BiblePresetEntry(Base):
    """One account-code row belonging to a BiblePreset."""

    __tablename__ = "bible_preset_entries"

    preset_id           = Column(Integer,     ForeignKey("bible_presets.id"), primary_key=True)
    account_code        = Column(String(20),  primary_key=True)
    description         = Column(Text,        nullable=False, default="")
    is_non_prov         = Column(Boolean,     nullable=False, default=False)
    prov_labour_pct     = Column(Float,       nullable=False, default=0.0)
    fed_labour_pct      = Column(Float,       nullable=False, default=0.0)
    prov_svc_labour_pct = Column(Float,       nullable=False, default=0.0)
    svc_property_pct    = Column(Float,       nullable=False, default=0.0)
    fed_svc_labour_pct  = Column(Float,       nullable=False, default=0.0)


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


class CashflowTemplateDistribution(Base):
    """Reusable distribution templates for cashflow by template name + account code."""

    __tablename__ = "cashflow_template_distributions"
    __table_args__ = (UniqueConstraint("template_name", "budget_code"),)

    id = Column(String(128), primary_key=True)  # "{template_name}::{budget_code}"
    template_name = Column(String(120), nullable=False, index=True)
    budget_code = Column(String(20), nullable=False)
    phase = Column(String(50), nullable=False)
    curve = Column(String(50), nullable=False)
    timing_pattern_override = Column(String(100), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
