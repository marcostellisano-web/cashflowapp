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


class ParsedBudget(BaseModel):
    """Result of parsing the uploaded Excel budget file."""

    line_items: list[BudgetLineItem]
    total_budget: float
    source_filename: str
    warnings: list[str] = []
