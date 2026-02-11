from datetime import date
from enum import Enum

from pydantic import BaseModel


class CurveType(str, Enum):
    FLAT = "flat"
    BELL = "bell"
    FRONT_LOADED = "front_loaded"
    BACK_LOADED = "back_loaded"
    S_CURVE = "s_curve"
    SHOOT_PROPORTIONAL = "shoot_proportional"
    MILESTONE = "milestone"


class PhaseAssignment(str, Enum):
    PREP = "prep"
    PRODUCTION = "production"
    POST = "post"
    DELIVERY = "delivery"
    FULL_SPAN = "full_span"
    PREP_AND_PRODUCTION = "prep_and_production"
    PRODUCTION_AND_POST = "production_and_post"


class LineItemDistribution(BaseModel):
    """How a single budget line should be distributed across time."""

    budget_code: str
    phase: PhaseAssignment
    curve: CurveType
    curve_params: dict | None = None
    milestone_dates: list[date] | None = None
    milestone_amounts: list[float] | None = None
    auto_assigned: bool = False
