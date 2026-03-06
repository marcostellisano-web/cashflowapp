from enum import Enum

from pydantic import BaseModel


class BudgetCategory(str, Enum):
    ABOVE_THE_LINE = "above_the_line"
    BELOW_THE_LINE_PRODUCTION = "below_the_line_production"
    BELOW_THE_LINE_POST = "below_the_line_post"
    OTHER = "other"


class BudgetLineItem(BaseModel):
    """A single row from the uploaded budget Excel."""

    code: str
    description: str
    total: float
    category: BudgetCategory | None = None
    account_group: str | None = None


class BudgetDetailRow(BaseModel):
    """A single detail row from the uploaded budget's Account Details sheet."""

    account: str
    description: str
    amount: float | None = None
    unit: str | None = None
    unit2: str | None = None
    currency: str | None = None
    rate: float | None = None
    unit3: str | None = None
    subtotal: float = 0.0
    # Fringe/aggregate percentage from the "Agg" column in Account Details (e.g. 0.15 = 15%)
    agg: float | None = None
    # Group label from the "Groups" column in Account Details (e.g. "Cast & Crew")
    groups: str | None = None


class ParsedBudget(BaseModel):
    """Result of parsing the uploaded Excel budget file."""

    line_items: list[BudgetLineItem]
    total_budget: float
    source_filename: str
    warnings: list[str] = []
    # Pre-aggregated totals keyed by 4-digit account code (e.g. "0100", "1200")
    # extracted from the source file's "Topsheet" tab when present.
    topsheet_totals: dict[str, float] = {}
    # Detail rows extracted from the source file's "Account Details" tab when present.
    detail_rows: list[BudgetDetailRow] = []
