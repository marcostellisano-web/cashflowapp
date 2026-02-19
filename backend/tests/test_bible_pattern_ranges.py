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


def test_prep_to_delivery_patterns_include_first_payroll_or_ap_week_after_final_delivery():
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
    next_payroll_after_delivery = next(
        i
        for i in range(delivery_idx + 1, len(weeks))
        if weeks[i].is_payroll_week is True
    )
    next_ap_after_delivery = next(
        i
        for i in range(delivery_idx + 1, len(weeks))
        if weeks[i].is_payroll_week is False
    )

    assert max(payroll_nonzero) == next_payroll_after_delivery
    assert max(ap_nonzero) == next_ap_after_delivery


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


def test_prep_to_delivery_uses_latest_episode_delivery_not_earlier_final_delivery_field():
    params = _params().model_copy(update={"final_delivery_date": date(2025, 5, 30)})
    weeks = build_timeline(params, end_date=date(2025, 7, 31))

    entry = BibleEntry(
        account_code="1205",
        description="PRODUCTION MANAGER",
        timing_pattern=TimingPattern.PREP_TO_DELIVERY_PAYROLL,
        timing_details="",
        timing_title="",
    )

    nonzero = _nonzero_weeks(distribute_bible_entry(1000, entry, weeks, params))

    true_final_delivery = max(ep.delivery_date for ep in params.episode_deliveries)
    true_delivery_idx = next(
        i for i, w in enumerate(weeks)
        if w.week_commencing <= true_final_delivery < (w.week_commencing + timedelta(days=7))
    )
    next_payroll_after_true_final = next(
        i for i in range(true_delivery_idx + 1, len(weeks))
        if weeks[i].is_payroll_week is True
    )

    assert nonzero
    assert max(nonzero) == next_payroll_after_true_final


def test_delivery_bound_patterns_use_true_final_episode_delivery_window():
    params = _params().model_copy(update={"final_delivery_date": date(2025, 5, 30)})
    weeks = build_timeline(params, end_date=date(2025, 8, 1))

    true_final_delivery = max(ep.delivery_date for ep in params.episode_deliveries)
    true_delivery_idx = next(
        i for i, w in enumerate(weeks)
        if w.week_commencing <= true_final_delivery < (w.week_commencing + timedelta(days=7))
    )

    entries = [
        BibleEntry(account_code="0410", description="SERIES PRODUCER", timing_pattern=TimingPattern.PREP_TO_DELIVERY_PAYROLL, timing_details="", timing_title=""),
        BibleEntry(account_code="0225", description="RESEARCH", timing_pattern=TimingPattern.PREP_TO_LAST_SHOOT_PAYROLL, timing_details="", timing_title=""),
        BibleEntry(account_code="0401", description="EXECUTIVE PRODUCER", timing_pattern=TimingPattern.INTERNALS, timing_details="", timing_title=""),
        BibleEntry(account_code="0220", description="SCRIPT EDITOR", timing_pattern=TimingPattern.PP_TO_END, timing_details="", timing_title=""),
        BibleEntry(account_code="7130", description="BANK CHARGES", timing_pattern=TimingPattern.PREP_TO_DELIVERY_AP, timing_details="", timing_title=""),
    ]

    for entry in entries:
        nonzero = _nonzero_weeks(distribute_bible_entry(1000, entry, weeks, params))
        assert nonzero, entry.account_code
        if entry.timing_pattern in {TimingPattern.PREP_TO_DELIVERY_PAYROLL, TimingPattern.PREP_TO_DELIVERY_AP}:
            # these include first cycle week after final delivery
            assert max(nonzero) > true_delivery_idx
        else:
            assert max(nonzero) <= true_delivery_idx
