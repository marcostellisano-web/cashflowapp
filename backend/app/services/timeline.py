"""Build a week-by-week production timeline from scheduling parameters."""

from datetime import date, timedelta

from app.domain.week_utils import count_weekdays_in_week, generate_week_mondays, is_date_in_ranges
from app.models.cashflow import WeekColumn
from app.models.production import ProductionParameters, ShootingBlock


def _find_active_block(monday: date, blocks: list[ShootingBlock]) -> ShootingBlock | None:
    """Find the shooting block active during a given week (by Monday)."""
    week_end = monday + timedelta(days=4)  # Friday
    for block in blocks:
        # A block is active in this week if any weekday overlaps
        if block.shoot_start <= week_end and block.shoot_end >= monday:
            return block
    return None


def _compute_shoot_days(monday: date, blocks: list[ShootingBlock]) -> int:
    """Count total shoot days (weekdays) in a given week across all active blocks."""
    total = 0
    for block in blocks:
        total += count_weekdays_in_week(monday, block.shoot_start, block.shoot_end)
    return total


def _determine_phase_label(
    monday: date,
    params: ProductionParameters,
) -> str:
    """Determine the phase label for a given week."""
    week_end = monday + timedelta(days=4)  # Friday

    # Check hiatus first
    if is_date_in_ranges(monday, params.hiatus_periods):
        return "HIATUS"

    # Check if in prep period
    in_prep = params.prep_start <= week_end and params.prep_end >= monday

    # Check shooting blocks
    active_block = _find_active_block(monday, params.shooting_blocks)

    # Check post-production
    post_start = params.post_start or (params.wrap_date + timedelta(days=1))
    in_post = post_start <= week_end and params.final_delivery_date >= monday

    # Check wrap (week containing wrap_date, after last shoot day)
    in_wrap = False
    if params.shooting_blocks:
        last_shoot = max(b.shoot_end for b in params.shooting_blocks)
        if last_shoot <= week_end and params.wrap_date >= monday:
            in_wrap = True

    # Priority: shooting > wrap > post > prep
    if active_block:
        eps = ", ".join(str(e) for e in active_block.episode_numbers)
        return f"SHOOT BLK {active_block.block_number} (Ep {eps})"

    if in_wrap and not in_post:
        return "WRAP"

    if in_post:
        # Try to label with specific episode post milestone
        for ep_del in params.episode_deliveries:
            if ep_del.rough_cut_date and ep_del.delivery_date:
                if ep_del.rough_cut_date <= week_end and ep_del.delivery_date >= monday:
                    return f"POST EP {ep_del.episode_number}"
        return "POST"

    if in_prep:
        return "PREP"

    return "PRE-PROD"


def build_timeline(params: ProductionParameters) -> list[WeekColumn]:
    """Build the full production timeline as a list of WeekColumns.

    Generates one WeekColumn per week from prep_start through final_delivery_date.
    Each week is labeled with its production phase and annotated with shoot day counts.
    """
    mondays = generate_week_mondays(params.prep_start, params.final_delivery_date)

    weeks: list[WeekColumn] = []
    for idx, monday in enumerate(mondays):
        is_hiatus = is_date_in_ranges(monday, params.hiatus_periods)
        shoot_days = 0 if is_hiatus else _compute_shoot_days(monday, params.shooting_blocks)
        phase_label = _determine_phase_label(monday, params)

        weeks.append(
            WeekColumn(
                week_number=idx + 1,
                week_commencing=monday,
                phase_label=phase_label,
                is_hiatus=is_hiatus,
                shoot_days=shoot_days,
            )
        )

    return weeks
