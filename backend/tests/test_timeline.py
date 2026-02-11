from datetime import date

from app.models.production import ProductionParameters, ShootingBlock, EpisodeDelivery
from app.services.timeline import build_timeline


def test_timeline_covers_full_production(sample_params):
    weeks = build_timeline(sample_params)
    assert len(weeks) > 0
    # First week should contain prep_start
    assert weeks[0].week_commencing <= sample_params.prep_start
    # Last week should contain final_delivery_date
    assert weeks[-1].week_commencing <= sample_params.final_delivery_date


def test_timeline_sequential_week_numbers(sample_params):
    weeks = build_timeline(sample_params)
    for i, week in enumerate(weeks):
        assert week.week_number == i + 1


def test_timeline_has_shoot_days_during_production(sample_params):
    weeks = build_timeline(sample_params)
    shoot_weeks = [w for w in weeks if w.shoot_days > 0]
    assert len(shoot_weeks) > 0


def test_timeline_no_shoot_days_during_prep(sample_params):
    weeks = build_timeline(sample_params)
    prep_weeks = [w for w in weeks if "PREP" in w.phase_label]
    for w in prep_weeks:
        assert w.shoot_days == 0


def test_timeline_phase_labels_present(sample_params):
    weeks = build_timeline(sample_params)
    labels = set(w.phase_label for w in weeks)
    # Should have at least PREP and SHOOT phases
    has_prep = any("PREP" in l for l in labels)
    has_shoot = any("SHOOT" in l for l in labels)
    assert has_prep
    assert has_shoot
