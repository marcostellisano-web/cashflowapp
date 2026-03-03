from datetime import date

from pydantic import BaseModel

from app.models.budget import ParsedBudget
from app.models.distribution import LineItemDistribution
from app.models.production import ProductionParameters

CASH_INFLOW_LABELS = [
    "Broadcaster 1",
    "Broadcaster 2",
    "Broadcaster 3",
    "CMF Funding",
    "Provincial Tax Credit",
    "Federal Tax Credit",
    "Distribution Guarantee",
]


class WeekColumn(BaseModel):
    """A single week in the cashflow timeline."""

    week_number: int
    week_commencing: date
    phase_label: str
    is_hiatus: bool = False
    shoot_days: int = 0
    is_payroll_week: bool | None = None  # None if no payroll cycle set


class CashflowRow(BaseModel):
    """A single budget line item's weekly distribution."""

    code: str
    description: str
    total: float
    weekly_amounts: list[float]


class CashInflowRow(BaseModel):
    """A single cash inflow source with weekly amounts."""

    label: str
    weekly_amounts: list[float]


class CashflowOutput(BaseModel):
    """The complete cashflow ready for Excel generation."""

    title: str
    weeks: list[WeekColumn]
    rows: list[CashflowRow]
    weekly_totals: list[float]
    cumulative_totals: list[float]
    grand_total: float
    cash_inflows: list[CashInflowRow] = []
    inflow_weekly_totals: list[float] = []
    inflow_cumulative_totals: list[float] = []


class GenerateRequest(BaseModel):
    """Request body for cashflow generation endpoints."""

    budget: ParsedBudget
    parameters: ProductionParameters
    distributions: list[LineItemDistribution]
