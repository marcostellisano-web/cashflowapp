from datetime import date, timedelta

from app.models.production import EpisodeDelivery, ProductionParameters, ShootingBlock
from app.models.timing_bible import BibleEntry, TimingPattern
from app.services.bible_distributor import distribute_bible_entry
from app.services.timeline import build_timeline


def _params() -> ProductionParameters:
    return ProductionParameters(
        title="Range Test",
        episode_count=2,
        prep_start=date(2025, 1, 6),
        pp_start=date(2025, 2, 17),
        pp_end=date(2025, 3, 28),
        edit_start=date(2025, 4, 7),
        shooting_blocks=[
            ShootingBlock(
                block_number=1,
                block_type="Shoot",
                episode_numbers=[1],
                shoot_start=date(2025, 2, 17),
                shoot_end=date(2025, 3, 7),
            ),
            ShootingBlock(
                block_number=2,
                block_type="Shoot",
                episode_numbers=[2],
                shoot_start=date(2025, 3, 10),
                shoot_end=date(2025, 3, 28),
            ),
        ],
        episode_deliveries=[
            EpisodeDelivery(
                episode_number=1,
                rough_cut_date=date(2025, 4, 25),
                picture_lock_date=date(2025, 5, 9),
                delivery_date=date(2025, 5, 30),
            ),
            EpisodeDelivery(
                episode_number=2,
                rough_cut_date=date(2025, 5, 2),
                picture_lock_date=date(2025, 5, 16),
                delivery_date=date(2025, 6, 6),
            ),
        ],
        final_delivery_date=date(2025, 6, 6),
        first_payroll_week=date(2025, 1, 6),
        hiatus_periods=[],
    )


def _nonzero_weeks(amounts):
    return [i for i, x in enumerate(amounts) if abs(float(x)) > 0.001]


def test_prep_to_delivery_patterns_stop_at_final_delivery_even_with_extended_timeline():
    params = _params()
    weeks = build_timeline(params, end_date=params.final_delivery_date + timedelta(weeks=6))

    payroll_entry = BibleEntry(
        account_code="0410",
        description="SERIES PRODUCER",
        timing_pattern=TimingPattern.PREP_TO_DELIVERY_PAYROLL,
        timing_details="",
        timing_title="",
    )
    ap_entry = BibleEntry(
        account_code="7130",
        description="BANK CHARGES",
        timing_pattern=TimingPattern.PREP_TO_DELIVERY_AP,
        timing_details="",
        timing_title="",
    )

    payroll_nonzero = _nonzero_weeks(distribute_bible_entry(1000, payroll_entry, weeks, params))
    ap_nonzero = _nonzero_weeks(distribute_bible_entry(1000, ap_entry, weeks, params))

    delivery_idx = next(i for i, w in enumerate(weeks) if w.week_commencing <= params.final_delivery_date < (w.week_commencing + timedelta(days=7)))

    assert payroll_nonzero and ap_nonzero
    assert max(payroll_nonzero) <= delivery_idx
    assert max(ap_nonzero) <= delivery_idx


def test_0220_pattern_uses_edit_minus_two_weeks_to_final_picture_lock():
    params = _params()
    weeks = build_timeline(params)
    entry = BibleEntry(
        account_code="0220",
        description="SCRIPT EDITOR(S)",
        timing_pattern=TimingPattern.EDIT_MINUS_2_TO_PIC_LOCK,
        timing_details="",
        timing_title="",
    )

    amounts = distribute_bible_entry(1000, entry, weeks, params)
    nonzero = _nonzero_weeks(amounts)

    start_date = params.edit_start - timedelta(weeks=2)
    start_idx = next(i for i, w in enumerate(weeks) if w.week_commencing <= start_date < (w.week_commencing + timedelta(days=7)))
    final_lock = max(ep.picture_lock_date for ep in params.episode_deliveries if ep.picture_lock_date)
    lock_idx = next(i for i, w in enumerate(weeks) if w.week_commencing <= final_lock < (w.week_commencing + timedelta(days=7)))

    assert nonzero
    assert min(nonzero) >= start_idx
    assert max(nonzero) <= lock_idx
