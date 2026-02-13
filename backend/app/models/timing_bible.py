"""Timing Bible models for TV production cashflow timing rules."""

from enum import Enum

from pydantic import BaseModel


class TimingPattern(str, Enum):
    """The distinct cashflow timing patterns used in TV production."""

    # Payroll-based patterns
    FULL_PAYROLL = "full_payroll"
    """Evenly on payroll weeks, full span (prep to delivery)."""

    PP_TO_END = "pp_to_end"
    """Evenly on payroll weeks from PP start to final delivery."""

    SHOOT_PAYROLL = "shoot_payroll"
    """Split by shoot weeks, payroll weeks, starts 1-2 weeks after shoot start."""

    EDIT_PAYROLL = "edit_payroll"
    """Evenly from edit start to final picture lock, payroll weeks."""

    ARCHIVE_RESEARCH = "archive_research"
    """Evenly over the edit period on payroll weeks."""

    ONLINE_EDITOR = "online_editor"
    """Split by online dates, paid 2-3 weeks after each online, payroll weeks."""

    COMPOSER = "composer"
    """2 pieces: midpoint of edit + final picture lock, payroll weeks."""

    STILL_PHOTO = "still_photo"
    """2-3 weeks after each shooting block, payroll weeks."""

    # AP-based patterns
    INTERNALS = "internals"
    """Monthly mid-month from prep to delivery, AP weeks."""

    EDIT_INTERNALS = "edit_internals"
    """Monthly mid-month over the edit period."""

    TRAVEL = "travel"
    """Split by blocks, paid 2-3 weeks before each block, AP weeks."""

    PER_DIEM = "per_diem"
    """Split by blocks, paid during shoot blocks, AP weeks."""

    SHOOT_PURCHASES = "shoot_purchases"
    """Split by blocks, paid during shoot blocks, AP weeks."""

    SHOOT_RENTALS = "shoot_rentals"
    """Split by shoot weeks, AP weeks, starts 1-2 weeks after shoot start."""

    MONTHLY_SHOOT = "monthly_shoot"
    """Monthly end-of-month during shoot, AP weeks."""

    PRE_SHOOT = "pre_shoot"
    """Lump sum 2-3 weeks before PP start, AP week."""

    LEGAL = "legal"
    """4 even chunks over production, AP weeks."""

    PICK_LOCK = "pick_lock"
    """Split by picture locks, paid 2-3 weeks after each, AP weeks."""

    DELIVERY_COPIES = "delivery_copies"
    """Split by deliveries, paid 2-3 weeks before each, AP weeks."""

    MIX = "mix"
    """2-3 weeks after each mix, AP weeks."""

    AFTER_DELIVERY = "after_delivery"
    """One month after final delivery, AP week."""

    GRAPHICS = "graphics"
    """3-4 weeks after edit start to final online, bi-weekly, AP weeks."""


class BibleEntry(BaseModel):
    """A single entry in the Cashflow Timing Bible."""

    account_code: str
    description: str
    timing_pattern: TimingPattern
    timing_details: str  # Human-readable description of the timing rule
    timing_title: str  # Category label (e.g. "Full Payroll", "Travel")


class TimingBible(BaseModel):
    """The complete Cashflow Timing Bible."""

    entries: list[BibleEntry]

    def get_entry(self, code: str) -> BibleEntry | None:
        """Look up a bible entry by account code."""
        for entry in self.entries:
            if entry.account_code == code:
                return entry
        return None

    def get_codes(self) -> list[str]:
        """Return all account codes in the bible."""
        return [e.account_code for e in self.entries]
