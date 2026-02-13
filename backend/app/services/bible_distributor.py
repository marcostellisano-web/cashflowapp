"""Bible-driven cashflow distribution engine.

Implements all timing patterns from the Cashflow Timing Bible. Each pattern
understands the production schedule (blocks, deliveries, milestones) and
respects the payroll/AP biweekly cycle.
"""

from datetime import date, timedelta

import numpy as np

from app.domain.week_utils import get_monday
from app.models.cashflow import WeekColumn
from app.models.production import ProductionParameters
from app.models.timing_bible import BibleEntry, TimingPattern


def distribute_bible_entry(
    total: float,
    entry: BibleEntry,
    weeks: list[WeekColumn],
    params: ProductionParameters,
) -> np.ndarray:
    """Distribute a budget line item using its bible timing pattern.

    Returns an array of length len(weeks) with weekly dollar amounts summing to `total`.
    """
    n = len(weeks)
    if n == 0 or total == 0:
        return np.zeros(n)

    pattern = entry.timing_pattern

    match pattern:
        case TimingPattern.FULL_PAYROLL:
            return _full_payroll(total, weeks, params)
        case TimingPattern.PP_TO_END:
            return _pp_to_end(total, weeks, params)
        case TimingPattern.SHOOT_PAYROLL:
            return _shoot_payroll(total, weeks, params)
        case TimingPattern.EDIT_PAYROLL:
            return _edit_payroll(total, weeks, params)
        case TimingPattern.ARCHIVE_RESEARCH:
            return _archive_research(total, weeks, params)
        case TimingPattern.ONLINE_EDITOR:
            return _online_editor(total, weeks, params)
        case TimingPattern.COMPOSER:
            return _composer(total, weeks, params)
        case TimingPattern.STILL_PHOTO:
            return _still_photo(total, weeks, params)
        case TimingPattern.INTERNALS:
            return _internals(total, weeks, params)
        case TimingPattern.EDIT_INTERNALS:
            return _edit_internals(total, weeks, params)
        case TimingPattern.TRAVEL:
            return _travel(total, weeks, params)
        case TimingPattern.PER_DIEM:
            return _per_diem(total, weeks, params)
        case TimingPattern.SHOOT_PURCHASES:
            return _shoot_purchases(total, weeks, params)
        case TimingPattern.SHOOT_RENTALS:
            return _shoot_rentals(total, weeks, params)
        case TimingPattern.MONTHLY_SHOOT:
            return _monthly_shoot(total, weeks, params)
        case TimingPattern.PRE_SHOOT:
            return _pre_shoot(total, weeks, params)
        case TimingPattern.LEGAL:
            return _legal(total, weeks, params)
        case TimingPattern.PICK_LOCK:
            return _pick_lock(total, weeks, params)
        case TimingPattern.DELIVERY_COPIES:
            return _delivery_copies(total, weeks, params)
        case TimingPattern.MIX:
            return _mix(total, weeks, params)
        case TimingPattern.AFTER_DELIVERY:
            return _after_delivery(total, weeks, params)
        case TimingPattern.GRAPHICS:
            return _graphics(total, weeks, params)
        case TimingPattern.INSURANCE:
            return _insurance(total, weeks, params)
        case TimingPattern.FULL_AP:
            return _full_ap(total, weeks, params)
        case TimingPattern.FINANCING:
            return _financing(total, weeks, params)

    # Fallback: flat across all weeks
    return _spread_flat(total, list(range(len(weeks))), len(weeks))


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _week_index_for_date(weeks: list[WeekColumn], target: date) -> int | None:
    """Find the week index containing a given date."""
    for i, w in enumerate(weeks):
        next_monday = w.week_commencing + timedelta(days=7)
        if w.week_commencing <= target < next_monday:
            return i
    return None


def _closest_week_index(weeks: list[WeekColumn], target: date) -> int:
    """Find the week index closest to a target date, clamped to valid range."""
    monday = get_monday(target)
    best = 0
    best_dist = abs((weeks[0].week_commencing - monday).days)
    for i, w in enumerate(weeks):
        dist = abs((w.week_commencing - monday).days)
        if dist < best_dist:
            best = i
            best_dist = dist
    return best


def _find_nearest_week_type(
    weeks: list[WeekColumn],
    target_idx: int,
    want_payroll: bool,
) -> int:
    """From target_idx, find the nearest week matching the desired payroll/AP type.

    Searches forward first, then backward. If no payroll cycle is set, returns target_idx.
    """
    n = len(weeks)
    if target_idx < 0:
        target_idx = 0
    if target_idx >= n:
        target_idx = n - 1

    # If no payroll cycle, return as-is
    if weeks[target_idx].is_payroll_week is None:
        return target_idx

    # Search outward from target
    for offset in range(n):
        for candidate in [target_idx + offset, target_idx - offset]:
            if 0 <= candidate < n:
                if weeks[candidate].is_payroll_week == want_payroll:
                    return candidate

    return target_idx


def _filter_by_week_type(
    weeks: list[WeekColumn],
    indices: list[int],
    want_payroll: bool,
) -> list[int]:
    """Filter week indices to only payroll or AP weeks.

    If no payroll cycle is configured, returns all indices unchanged.
    """
    if not indices:
        return indices
    # Check if payroll cycle is configured
    if weeks[indices[0]].is_payroll_week is None:
        return indices
    return [i for i in indices if weeks[i].is_payroll_week == want_payroll]


def _spread_flat(total: float, indices: list[int], n_weeks: int) -> np.ndarray:
    """Spread total evenly across the given week indices."""
    result = np.zeros(n_weeks)
    if not indices:
        return result
    per_week = total / len(indices)
    for i in indices:
        result[i] = per_week
    return result


def _spread_at_indices(
    total: float,
    target_indices: list[int],
    n_weeks: int,
) -> np.ndarray:
    """Spread total evenly across specific target week indices (milestone-style)."""
    result = np.zeros(n_weeks)
    if not target_indices:
        return result
    per_hit = total / len(target_indices)
    for i in target_indices:
        result[i] = per_hit
    return result


def _get_shoot_week_indices(weeks: list[WeekColumn]) -> list[int]:
    """Return indices of weeks with shooting activity (phase label contains SHOOT)."""
    return [i for i, w in enumerate(weeks) if "SHOOT" in w.phase_label.upper()]


def _get_all_non_hiatus(weeks: list[WeekColumn]) -> list[int]:
    """Return indices of all non-hiatus weeks."""
    return [i for i, w in enumerate(weeks) if not w.is_hiatus]


def _offset_weeks(base_idx: int, offset: int, n_weeks: int) -> int:
    """Apply a week offset, clamped to valid range."""
    return max(0, min(n_weeks - 1, base_idx + offset))


def _get_monthly_midmonth_weeks(
    weeks: list[WeekColumn],
    start_date: date,
    end_date: date,
) -> list[int]:
    """Find week indices that contain the ~15th of each month in a date range.

    Returns one index per calendar month spanned.
    """
    indices = []
    current = date(start_date.year, start_date.month, 15)
    if current < start_date:
        # Move to next month's 15th
        if current.month == 12:
            current = date(current.year + 1, 1, 15)
        else:
            current = date(current.year, current.month + 1, 15)

    while current <= end_date + timedelta(days=14):
        idx = _week_index_for_date(weeks, current)
        if idx is not None:
            indices.append(idx)
        # Advance to next month
        if current.month == 12:
            current = date(current.year + 1, 1, 15)
        else:
            current = date(current.year, current.month + 1, 15)

    return indices


def _get_monthly_endmonth_weeks(
    weeks: list[WeekColumn],
    start_date: date,
    end_date: date,
) -> list[int]:
    """Find week indices that contain the last weekday of each month in a date range."""
    indices = []
    # Start from the month of start_date
    current_year, current_month = start_date.year, start_date.month

    while True:
        # Last day of this month
        if current_month == 12:
            last_day = date(current_year, 12, 31)
        else:
            last_day = date(current_year, current_month + 1, 1) - timedelta(days=1)

        # Back up to last weekday
        while last_day.weekday() > 4:  # Sat=5, Sun=6
            last_day -= timedelta(days=1)

        if last_day > end_date + timedelta(days=14):
            break

        if last_day >= start_date - timedelta(days=7):
            idx = _week_index_for_date(weeks, last_day)
            if idx is not None:
                indices.append(idx)

        # Next month
        if current_month == 12:
            current_year += 1
            current_month = 1
        else:
            current_month += 1

    return indices


# ---------------------------------------------------------------------------
# Timing pattern implementations
# ---------------------------------------------------------------------------

def _full_payroll(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Evenly on payroll weeks, full span (prep to delivery)."""
    all_weeks = _get_all_non_hiatus(weeks)
    payroll_weeks = _filter_by_week_type(weeks, all_weeks, want_payroll=True)
    return _spread_flat(total, payroll_weeks, len(weeks))


def _pp_to_end(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Evenly on payroll weeks from PP start to final delivery."""
    pp_start_idx = _week_index_for_date(weeks, params.pp_start)
    if pp_start_idx is None:
        pp_start_idx = 0
    indices = [i for i in range(pp_start_idx, len(weeks)) if not weeks[i].is_hiatus]
    payroll_weeks = _filter_by_week_type(weeks, indices, want_payroll=True)
    return _spread_flat(total, payroll_weeks, len(weeks))


def _shoot_payroll(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Weekly during shoot, on payroll weeks, starting 1-2 weeks after shoot start.

    The 1-2 week offset accounts for payroll lag.
    """
    shoot_indices = _get_shoot_week_indices(weeks)
    if not shoot_indices:
        return _spread_flat(total, _get_all_non_hiatus(weeks), len(weeks))

    # Offset by 1 week (payroll lag)
    first_shoot = shoot_indices[0]
    offset_start = _offset_weeks(first_shoot, 1, len(weeks))

    # Include shoot weeks + 1-2 weeks after last shoot for final pay runs
    last_shoot = shoot_indices[-1]
    offset_end = _offset_weeks(last_shoot, 2, len(weeks))

    candidate = [i for i in range(offset_start, offset_end + 1) if not weeks[i].is_hiatus]
    payroll = _filter_by_week_type(weeks, candidate, want_payroll=True)
    return _spread_flat(total, payroll, len(weeks))


def _edit_payroll(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Evenly from edit start to final picture lock, on payroll weeks."""
    edit_idx = _week_index_for_date(weeks, params.edit_start)
    if edit_idx is None:
        edit_idx = 0

    # Final picture lock = latest picture_lock_date across all episodes
    pic_locks = [ep.picture_lock_date for ep in params.episode_deliveries if ep.picture_lock_date]
    if pic_locks:
        final_lock = max(pic_locks)
        lock_idx = _week_index_for_date(weeks, final_lock)
        if lock_idx is None:
            lock_idx = len(weeks) - 1
    else:
        # Fallback: use final delivery
        lock_idx = len(weeks) - 1

    candidate = [i for i in range(edit_idx, lock_idx + 1) if not weeks[i].is_hiatus]
    payroll = _filter_by_week_type(weeks, candidate, want_payroll=True)
    return _spread_flat(total, payroll, len(weeks))


def _archive_research(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Evenly over the edit period on payroll weeks (edit start to final delivery)."""
    edit_idx = _week_index_for_date(weeks, params.edit_start)
    if edit_idx is None:
        edit_idx = 0

    candidate = [i for i in range(edit_idx, len(weeks)) if not weeks[i].is_hiatus]
    payroll = _filter_by_week_type(weeks, candidate, want_payroll=True)
    return _spread_flat(total, payroll, len(weeks))


def _online_editor(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Split by online dates, paid 2-3 weeks after each online, on payroll weeks."""
    online_dates = [ep.online_date for ep in params.episode_deliveries if ep.online_date]
    if not online_dates:
        # Fallback to edit period
        return _archive_research(total, weeks, params)

    n = len(weeks)
    targets = []
    for od in online_dates:
        base = _week_index_for_date(weeks, od)
        if base is None:
            base = _closest_week_index(weeks, od)
        offset_idx = _offset_weeks(base, 2, n)
        targets.append(_find_nearest_week_type(weeks, offset_idx, want_payroll=True))

    return _spread_at_indices(total, targets, n)


def _composer(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """2 pieces: midpoint of edit + final picture lock, on payroll weeks."""
    n = len(weeks)
    edit_idx = _week_index_for_date(weeks, params.edit_start) or 0

    pic_locks = [ep.picture_lock_date for ep in params.episode_deliveries if ep.picture_lock_date]
    if pic_locks:
        final_lock = max(pic_locks)
        lock_idx = _week_index_for_date(weeks, final_lock)
        if lock_idx is None:
            lock_idx = n - 1
    else:
        lock_idx = n - 1

    # Midpoint of edit period
    mid_idx = (edit_idx + lock_idx) // 2

    target1 = _find_nearest_week_type(weeks, mid_idx, want_payroll=True)
    target2 = _find_nearest_week_type(weeks, lock_idx, want_payroll=True)

    return _spread_at_indices(total, [target1, target2], n)


def _still_photo(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """2-3 weeks after each shooting block, on payroll weeks."""
    n = len(weeks)
    targets = []
    for block in params.shooting_blocks:
        base = _week_index_for_date(weeks, block.shoot_end)
        if base is None:
            base = _closest_week_index(weeks, block.shoot_end)
        offset_idx = _offset_weeks(base, 2, n)
        targets.append(_find_nearest_week_type(weeks, offset_idx, want_payroll=True))

    if not targets:
        return _spread_flat(total, _get_all_non_hiatus(weeks), n)
    return _spread_at_indices(total, targets, n)


def _internals(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Monthly mid-month from prep to delivery, on AP weeks."""
    monthly = _get_monthly_midmonth_weeks(weeks, params.prep_start, params.final_delivery_date)
    ap_monthly = [
        _find_nearest_week_type(weeks, idx, want_payroll=False)
        for idx in monthly
    ]
    if not ap_monthly:
        all_weeks = _get_all_non_hiatus(weeks)
        return _spread_flat(total, _filter_by_week_type(weeks, all_weeks, want_payroll=False), len(weeks))
    return _spread_at_indices(total, ap_monthly, len(weeks))


def _edit_internals(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Monthly mid-month over the edit period."""
    # Edit period: edit_start to final_delivery_date
    monthly = _get_monthly_midmonth_weeks(weeks, params.edit_start, params.final_delivery_date)
    ap_monthly = [
        _find_nearest_week_type(weeks, idx, want_payroll=False)
        for idx in monthly
    ]
    if not ap_monthly:
        edit_idx = _week_index_for_date(weeks, params.edit_start) or 0
        candidate = [i for i in range(edit_idx, len(weeks)) if not weeks[i].is_hiatus]
        return _spread_flat(total, _filter_by_week_type(weeks, candidate, want_payroll=False), len(weeks))
    return _spread_at_indices(total, ap_monthly, len(weeks))


def _travel(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Split by blocks, paid 2-3 weeks before each block start, on AP weeks."""
    n = len(weeks)
    targets = []
    for block in params.shooting_blocks:
        base = _week_index_for_date(weeks, block.shoot_start)
        if base is None:
            base = _closest_week_index(weeks, block.shoot_start)
        offset_idx = _offset_weeks(base, -2, n)
        targets.append(_find_nearest_week_type(weeks, offset_idx, want_payroll=False))

    if not targets:
        return _spread_flat(total, _get_all_non_hiatus(weeks), n)
    return _spread_at_indices(total, targets, n)


def _per_diem(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Split by blocks, paid during each shoot block, on AP weeks.

    Total is split evenly across blocks. Within each block, the amount lands on
    the AP week(s) during the block.
    """
    n = len(weeks)
    if not params.shooting_blocks:
        return _spread_flat(total, _get_all_non_hiatus(weeks), n)

    result = np.zeros(n)
    per_block = total / len(params.shooting_blocks)

    for block in params.shooting_blocks:
        # Find weeks during this block
        block_weeks = []
        for i, w in enumerate(weeks):
            week_end = w.week_commencing + timedelta(days=4)
            if block.shoot_start <= week_end and block.shoot_end >= w.week_commencing:
                block_weeks.append(i)

        ap_weeks = _filter_by_week_type(weeks, block_weeks, want_payroll=False)
        if not ap_weeks:
            # No AP weeks during block — use the nearest AP week after block
            block_end_idx = _week_index_for_date(weeks, block.shoot_end)
            if block_end_idx is None:
                block_end_idx = _closest_week_index(weeks, block.shoot_end)
            ap_weeks = [_find_nearest_week_type(weeks, block_end_idx, want_payroll=False)]

        per_week = per_block / len(ap_weeks)
        for idx in ap_weeks:
            result[idx] += per_week

    return result


def _shoot_purchases(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Split by blocks, paid during shoot blocks, on AP weeks. Same logic as per_diem."""
    return _per_diem(total, weeks, params)


def _shoot_rentals(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Weekly during shoot, on AP weeks, starting 1-2 weeks after shoot start.

    Same shape as shoot_payroll but on AP weeks.
    """
    shoot_indices = _get_shoot_week_indices(weeks)
    if not shoot_indices:
        return _spread_flat(total, _get_all_non_hiatus(weeks), len(weeks))

    first_shoot = shoot_indices[0]
    offset_start = _offset_weeks(first_shoot, 1, len(weeks))
    last_shoot = shoot_indices[-1]
    offset_end = _offset_weeks(last_shoot, 2, len(weeks))

    candidate = [i for i in range(offset_start, offset_end + 1) if not weeks[i].is_hiatus]
    ap = _filter_by_week_type(weeks, candidate, want_payroll=False)
    return _spread_flat(total, ap, len(weeks))


def _monthly_shoot(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Monthly end-of-month during shoot period, on AP weeks."""
    if not params.shooting_blocks:
        return _spread_flat(total, _get_all_non_hiatus(weeks), len(weeks))

    shoot_start = min(b.shoot_start for b in params.shooting_blocks)
    shoot_end = max(b.shoot_end for b in params.shooting_blocks)

    monthly = _get_monthly_endmonth_weeks(weeks, shoot_start, shoot_end)
    ap_monthly = [
        _find_nearest_week_type(weeks, idx, want_payroll=False)
        for idx in monthly
    ]
    if not ap_monthly:
        shoot_indices = _get_shoot_week_indices(weeks)
        return _spread_flat(total, _filter_by_week_type(weeks, shoot_indices, want_payroll=False), len(weeks))
    return _spread_at_indices(total, ap_monthly, len(weeks))


def _pre_shoot(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Lump sum 2-3 weeks before PP start, on AP week."""
    n = len(weeks)
    pp_idx = _week_index_for_date(weeks, params.pp_start)
    if pp_idx is None:
        pp_idx = _closest_week_index(weeks, params.pp_start)

    target = _offset_weeks(pp_idx, -2, n)
    target = _find_nearest_week_type(weeks, target, want_payroll=False)
    return _spread_at_indices(total, [target], n)


def _legal(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """4 even chunks over the course of production, on AP weeks.

    Spaced approximately quarterly: a few weeks after prep, ~1/4, ~1/2, ~3/4 through,
    and a few weeks after delivery.
    """
    n = len(weeks)
    all_non_hiatus = _get_all_non_hiatus(weeks)
    if not all_non_hiatus:
        return np.zeros(n)

    total_span = len(all_non_hiatus)
    # 4 evenly spaced points, offset slightly from edges
    offsets = [
        max(2, total_span // 8),
        total_span // 4 + total_span // 8,
        total_span // 2 + total_span // 8,
        min(total_span - 1, total_span - max(2, total_span // 8)),
    ]

    targets = []
    for off in offsets:
        idx = all_non_hiatus[min(off, total_span - 1)]
        targets.append(_find_nearest_week_type(weeks, idx, want_payroll=False))

    return _spread_at_indices(total, targets, n)


def _pick_lock(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Split by picture locks, paid 2-3 weeks after each, on AP weeks."""
    n = len(weeks)
    pic_locks = [ep.picture_lock_date for ep in params.episode_deliveries if ep.picture_lock_date]
    if not pic_locks:
        return _edit_internals(total, weeks, params)

    targets = []
    for pl in pic_locks:
        base = _week_index_for_date(weeks, pl)
        if base is None:
            base = _closest_week_index(weeks, pl)
        offset_idx = _offset_weeks(base, 2, n)
        targets.append(_find_nearest_week_type(weeks, offset_idx, want_payroll=False))

    return _spread_at_indices(total, targets, n)


def _delivery_copies(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Split by deliveries, paid 2-3 weeks before each delivery, on AP weeks."""
    n = len(weeks)
    targets = []
    for ep in params.episode_deliveries:
        base = _week_index_for_date(weeks, ep.delivery_date)
        if base is None:
            base = _closest_week_index(weeks, ep.delivery_date)
        offset_idx = _offset_weeks(base, -2, n)
        targets.append(_find_nearest_week_type(weeks, offset_idx, want_payroll=False))

    if not targets:
        return _spread_flat(total, _get_all_non_hiatus(weeks), n)
    return _spread_at_indices(total, targets, n)


def _mix(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """2-3 weeks after each mix, on AP weeks."""
    n = len(weeks)
    mix_dates = [ep.mix_date for ep in params.episode_deliveries if ep.mix_date]
    if not mix_dates:
        # Fallback: use delivery dates with slight offset
        return _delivery_copies(total, weeks, params)

    targets = []
    for md in mix_dates:
        base = _week_index_for_date(weeks, md)
        if base is None:
            base = _closest_week_index(weeks, md)
        offset_idx = _offset_weeks(base, 2, n)
        targets.append(_find_nearest_week_type(weeks, offset_idx, want_payroll=False))

    return _spread_at_indices(total, targets, n)


def _after_delivery(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """One month after final delivery, on AP week.

    If the timeline doesn't extend that far, use the last available AP week.
    """
    n = len(weeks)
    target_date = params.final_delivery_date + timedelta(weeks=4)
    idx = _week_index_for_date(weeks, target_date)
    if idx is None:
        # Timeline may not extend that far — use the very last week
        idx = n - 1
    target = _find_nearest_week_type(weeks, idx, want_payroll=False)
    return _spread_at_indices(total, [target], n)


def _graphics(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """3-4 weeks after edit start to final online, bi-weekly, on AP weeks."""
    n = len(weeks)
    edit_idx = _week_index_for_date(weeks, params.edit_start)
    if edit_idx is None:
        edit_idx = 0

    # Start 3 weeks after edit
    start_idx = _offset_weeks(edit_idx, 3, n)

    # End at final online
    online_dates = [ep.online_date for ep in params.episode_deliveries if ep.online_date]
    if online_dates:
        final_online = max(online_dates)
        end_idx = _week_index_for_date(weeks, final_online)
        if end_idx is None:
            end_idx = n - 1
    else:
        end_idx = n - 1

    # Bi-weekly = every other week within the range
    candidate = []
    for i in range(start_idx, end_idx + 1):
        if not weeks[i].is_hiatus:
            candidate.append(i)

    # Pick every other week from the candidates
    biweekly = candidate[::2]

    # Filter to AP weeks
    ap = _filter_by_week_type(weeks, biweekly, want_payroll=False)
    if not ap:
        ap = _filter_by_week_type(weeks, candidate, want_payroll=False)

    return _spread_flat(total, ap, n)


def _insurance(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Lump sum 2-3 weeks after prep start, on AP week."""
    n = len(weeks)
    prep_idx = _week_index_for_date(weeks, params.prep_start)
    if prep_idx is None:
        prep_idx = 0
    target = _offset_weeks(prep_idx, 2, n)
    target = _find_nearest_week_type(weeks, target, want_payroll=False)
    return _spread_at_indices(total, [target], n)


def _full_ap(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Evenly over the course of production on AP weeks."""
    all_weeks = _get_all_non_hiatus(weeks)
    ap_weeks = _filter_by_week_type(weeks, all_weeks, want_payroll=False)
    return _spread_flat(total, ap_weeks, len(weeks))


def _financing(total: float, weeks: list[WeekColumn], params: ProductionParameters) -> np.ndarray:
    """Paid at fiscal year-end (October), pro-rated by spend in each fiscal year.

    Finds each October 31 that falls within the production timeline. The total
    is split proportionally by how many production weeks fall in each fiscal
    year (Nov 1 - Oct 31). Each chunk lands on the AP week nearest Oct 31.
    """
    n = len(weeks)
    if n == 0:
        return np.zeros(n)

    first_monday = weeks[0].week_commencing
    last_monday = weeks[-1].week_commencing

    # Find all Oct 31 dates within (or near) the timeline
    oct_dates = []
    year = first_monday.year
    while True:
        oct31 = date(year, 10, 31)
        # Back up to last weekday if it falls on a weekend
        while oct31.weekday() > 4:
            oct31 -= timedelta(days=1)
        if oct31 > last_monday + timedelta(days=60):
            break
        if oct31 >= first_monday - timedelta(days=30):
            oct_dates.append(oct31)
        year += 1

    if not oct_dates:
        # No fiscal year-end in timeline — put it on the last AP week
        all_weeks = _get_all_non_hiatus(weeks)
        ap = _filter_by_week_type(weeks, all_weeks, want_payroll=False)
        return _spread_at_indices(total, [ap[-1]] if ap else [n - 1], n)

    # Count production weeks in each fiscal year segment
    all_non_hiatus = _get_all_non_hiatus(weeks)
    segment_counts = []
    boundaries = [first_monday] + [date(d.year, 11, 1) for d in oct_dates]

    for seg_idx in range(len(oct_dates)):
        seg_start = boundaries[seg_idx]
        seg_end = oct_dates[seg_idx] + timedelta(days=6)
        count = sum(
            1 for i in all_non_hiatus
            if seg_start <= weeks[i].week_commencing <= seg_end
        )
        segment_counts.append(count)

    # Handle weeks after the last October
    if boundaries[-1] <= last_monday:
        remaining = sum(
            1 for i in all_non_hiatus
            if weeks[i].week_commencing >= boundaries[-1]
        )
        if remaining > 0 and len(oct_dates) > 0:
            segment_counts[-1] += remaining

    total_counted = sum(segment_counts)
    if total_counted == 0:
        total_counted = 1

    result = np.zeros(n)
    for seg_idx, oct_d in enumerate(oct_dates):
        proportion = segment_counts[seg_idx] / total_counted
        amount = total * proportion
        idx = _week_index_for_date(weeks, oct_d)
        if idx is None:
            idx = _closest_week_index(weeks, oct_d)
        target = _find_nearest_week_type(weeks, idx, want_payroll=False)
        result[target] += amount

    return result
