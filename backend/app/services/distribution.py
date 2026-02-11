"""Distribution curve generators for spreading budget across weeks."""

import numpy as np
from scipy.stats import beta, norm

from app.models.distribution import CurveType


def generate_weights(curve_type: CurveType, num_weeks: int, params: dict | None = None) -> np.ndarray:
    """Generate normalized distribution weights for N weeks.

    All returned arrays sum to 1.0 (or are all-zero if num_weeks <= 0).

    Args:
        curve_type: The type of distribution curve.
        num_weeks: Number of weeks to distribute across.
        params: Optional parameters to tune the curve shape.

    Returns:
        numpy array of weights summing to 1.0.
    """
    if num_weeks <= 0:
        return np.array([])

    if num_weeks == 1:
        return np.array([1.0])

    p = params or {}
    x = np.linspace(0, 1, num_weeks)

    if curve_type == CurveType.FLAT:
        weights = np.ones(num_weeks)

    elif curve_type == CurveType.BELL:
        sigma = p.get("sigma", 0.2)
        weights = norm.pdf(x, loc=0.5, scale=sigma)

    elif curve_type == CurveType.FRONT_LOADED:
        a = p.get("a", 2.0)
        b = p.get("b", 5.0)
        weights = beta.pdf(x, a, b)
        # Handle edge case: beta.pdf can return inf at boundaries
        weights = np.nan_to_num(weights, nan=0.0, posinf=0.0)

    elif curve_type == CurveType.BACK_LOADED:
        a = p.get("a", 5.0)
        b = p.get("b", 2.0)
        weights = beta.pdf(x, a, b)
        weights = np.nan_to_num(weights, nan=0.0, posinf=0.0)

    elif curve_type == CurveType.S_CURVE:
        sigma = p.get("sigma", 0.15)
        cumulative = norm.cdf(x, loc=0.5, scale=sigma)
        weights = np.diff(cumulative, prepend=0)
        weights = np.maximum(weights, 0)

    elif curve_type == CurveType.SHOOT_PROPORTIONAL:
        # Placeholder — actual weights are injected by cashflow_engine
        # based on shoot days per week
        weights = np.ones(num_weeks)

    elif curve_type == CurveType.MILESTONE:
        # Placeholder — actual weights are computed by cashflow_engine
        # based on milestone dates
        weights = np.zeros(num_weeks)
        if num_weeks > 0:
            weights[-1] = 1.0  # Default: lump sum at end

    else:
        weights = np.ones(num_weeks)

    # Normalize
    total = weights.sum()
    if total > 0:
        weights = weights / total
    elif num_weeks > 0:
        # Fallback: even distribution if all weights are zero
        weights = np.ones(num_weeks) / num_weeks

    return weights


def generate_shoot_proportional_weights(shoot_days_per_week: list[int]) -> np.ndarray:
    """Generate weights proportional to shoot days per week.

    Args:
        shoot_days_per_week: List of shoot day counts, one per week.

    Returns:
        Normalized weight array.
    """
    weights = np.array(shoot_days_per_week, dtype=float)
    total = weights.sum()
    if total > 0:
        return weights / total
    return np.ones(len(shoot_days_per_week)) / max(len(shoot_days_per_week), 1)


def generate_milestone_weights(
    num_weeks: int,
    milestone_week_indices: list[int],
    milestone_amounts: list[float] | None = None,
) -> np.ndarray:
    """Generate weights for milestone-based distribution.

    If milestone_amounts are provided, they are used as raw amounts (not normalized).
    If not, the total is split evenly across milestone dates.

    Args:
        num_weeks: Total number of weeks in the distribution range.
        milestone_week_indices: Week indices (0-based) where milestones occur.
        milestone_amounts: Optional specific amounts for each milestone.

    Returns:
        Weight array (normalized to sum to 1.0 if no specific amounts).
    """
    weights = np.zeros(num_weeks)

    if not milestone_week_indices:
        # No milestones — put everything in the last week
        if num_weeks > 0:
            weights[-1] = 1.0
        return weights

    if milestone_amounts and len(milestone_amounts) == len(milestone_week_indices):
        total_amount = sum(milestone_amounts)
        for idx, amount in zip(milestone_week_indices, milestone_amounts):
            if 0 <= idx < num_weeks:
                weights[idx] = amount / total_amount if total_amount > 0 else 0
    else:
        # Even split across milestones
        share = 1.0 / len(milestone_week_indices)
        for idx in milestone_week_indices:
            if 0 <= idx < num_weeks:
                weights[idx] = share

    return weights
