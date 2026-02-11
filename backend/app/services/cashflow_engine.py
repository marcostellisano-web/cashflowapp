"""Core cashflow generation engine.

Orchestrates timeline building, distribution assignment, and budget spreading
to produce a complete weekly cashflow output.
"""

from datetime import date

import numpy as np

from app.models.budget import ParsedBudget
from app.models.cashflow import CashflowOutput, CashflowRow, WeekColumn
from app.models.distribution import CurveType, LineItemDistribution, PhaseAssignment
from app.models.production import ProductionParameters
from app.services.distribution import (
    generate_milestone_weights,
    generate_shoot_proportional_weights,
    generate_weights,
)
from app.services.phase_mapper import merge_distributions
from app.services.timeline import build_timeline


def _get_phase_week_indices(
    weeks: list[WeekColumn],
    phase: PhaseAssignment,
    params: ProductionParameters,
) -> list[int]:
    """Return indices of weeks that belong to the given phase assignment."""
    indices = []

    for i, week in enumerate(weeks):
        if week.is_hiatus:
            continue

        label = week.phase_label.upper()
        monday = week.week_commencing

        match phase:
            case PhaseAssignment.PREP:
                if "PREP" in label:
                    indices.append(i)

            case PhaseAssignment.PRODUCTION:
                if "SHOOT" in label or "WRAP" in label:
                    indices.append(i)

            case PhaseAssignment.POST:
                if "POST" in label:
                    indices.append(i)

            case PhaseAssignment.DELIVERY:
                if "POST" in label or "DELIVERY" in label:
                    indices.append(i)

            case PhaseAssignment.FULL_SPAN:
                indices.append(i)

            case PhaseAssignment.PREP_AND_PRODUCTION:
                if "PREP" in label or "SHOOT" in label or "WRAP" in label:
                    indices.append(i)

            case PhaseAssignment.PRODUCTION_AND_POST:
                if "SHOOT" in label or "WRAP" in label or "POST" in label:
                    indices.append(i)

    return indices


def _resolve_milestone_week_indices(
    weeks: list[WeekColumn],
    milestone_dates: list[date] | None,
    phase_indices: list[int],
) -> list[int]:
    """Map milestone dates to their corresponding week indices."""
    if not milestone_dates:
        # Default: last week of the phase
        return [phase_indices[-1]] if phase_indices else []

    result = []
    for m_date in milestone_dates:
        # Find the week that contains this date
        for i, week in enumerate(weeks):
            week_end = week.week_commencing
            # A date falls in a week if it's >= Monday and < next Monday
            from datetime import timedelta

            next_monday = week.week_commencing + timedelta(days=7)
            if week.week_commencing <= m_date < next_monday:
                result.append(i)
                break
        else:
            # Date not found in any week — use closest phase week
            if phase_indices:
                result.append(phase_indices[-1])

    return result


def generate_cashflow(
    budget: ParsedBudget,
    parameters: ProductionParameters,
    distributions: list[LineItemDistribution],
) -> CashflowOutput:
    """Generate a complete cashflow from budget, parameters, and distributions.

    Args:
        budget: Parsed budget with line items.
        parameters: Production scheduling parameters.
        distributions: User and/or auto-assigned distribution configs per budget line.

    Returns:
        CashflowOutput with all rows, weekly/cumulative totals.
    """
    # Build timeline
    weeks = build_timeline(parameters)
    num_weeks = len(weeks)

    # Merge user distributions with auto-assigned defaults
    all_codes = [item.code for item in budget.line_items]
    merged_dists = merge_distributions(all_codes, distributions)
    dist_map = {d.budget_code: d for d in merged_dists}

    # Generate cashflow rows
    rows: list[CashflowRow] = []
    weekly_totals = np.zeros(num_weeks)

    for item in budget.line_items:
        dist = dist_map.get(item.code)
        if dist is None:
            # Shouldn't happen after merge, but handle gracefully
            weekly_amounts = np.zeros(num_weeks)
        else:
            weekly_amounts = _distribute_line_item(
                total=item.total,
                dist=dist,
                weeks=weeks,
                params=parameters,
                num_weeks=num_weeks,
            )

        weekly_totals += weekly_amounts

        rows.append(
            CashflowRow(
                code=item.code,
                description=item.description,
                total=item.total,
                weekly_amounts=[round(a, 2) for a in weekly_amounts.tolist()],
            )
        )

    # Compute cumulative totals
    cumulative = np.cumsum(weekly_totals)

    return CashflowOutput(
        title=parameters.title,
        weeks=weeks,
        rows=rows,
        weekly_totals=[round(t, 2) for t in weekly_totals.tolist()],
        cumulative_totals=[round(c, 2) for c in cumulative.tolist()],
        grand_total=round(float(weekly_totals.sum()), 2),
    )


def _distribute_line_item(
    total: float,
    dist: LineItemDistribution,
    weeks: list[WeekColumn],
    params: ProductionParameters,
    num_weeks: int,
) -> np.ndarray:
    """Distribute a single budget line item across the timeline.

    Returns an array of length num_weeks with the weekly amounts.
    """
    weekly_amounts = np.zeros(num_weeks)

    # Get phase-relevant week indices
    phase_indices = _get_phase_week_indices(weeks, dist.phase, params)
    if not phase_indices:
        # No relevant weeks — spread evenly across all non-hiatus weeks
        phase_indices = [i for i, w in enumerate(weeks) if not w.is_hiatus]
        if not phase_indices:
            return weekly_amounts

    n_phase_weeks = len(phase_indices)

    # Generate weights based on curve type
    if dist.curve == CurveType.SHOOT_PROPORTIONAL:
        shoot_days = [weeks[i].shoot_days for i in phase_indices]
        if sum(shoot_days) == 0:
            # No shoot days in these weeks — fall back to flat
            weights = generate_weights(CurveType.FLAT, n_phase_weeks)
        else:
            weights = generate_shoot_proportional_weights(shoot_days)

    elif dist.curve == CurveType.MILESTONE:
        milestone_indices = _resolve_milestone_week_indices(
            weeks, dist.milestone_dates, phase_indices
        )
        # Convert global indices to local phase indices
        phase_set = set(phase_indices)
        local_milestone = []
        for gi in milestone_indices:
            if gi in phase_set:
                local_milestone.append(phase_indices.index(gi))
            elif phase_indices:
                # Find closest phase week
                closest = min(phase_indices, key=lambda pi: abs(pi - gi))
                local_milestone.append(phase_indices.index(closest))

        weights = generate_milestone_weights(
            n_phase_weeks,
            local_milestone,
            dist.milestone_amounts,
        )
    else:
        weights = generate_weights(dist.curve, n_phase_weeks, dist.curve_params)

    # Apply weights to the total and place in the correct week positions
    amounts = total * weights
    for local_idx, global_idx in enumerate(phase_indices):
        weekly_amounts[global_idx] = amounts[local_idx]

    return weekly_amounts
