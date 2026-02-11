import numpy as np
import pytest

from app.models.distribution import CurveType
from app.services.distribution import (
    generate_milestone_weights,
    generate_shoot_proportional_weights,
    generate_weights,
)


class TestGenerateWeights:
    def test_flat_weights_sum_to_one(self):
        weights = generate_weights(CurveType.FLAT, 10)
        assert len(weights) == 10
        assert abs(weights.sum() - 1.0) < 1e-10

    def test_flat_weights_are_equal(self):
        weights = generate_weights(CurveType.FLAT, 5)
        assert np.allclose(weights, 0.2)

    def test_bell_weights_sum_to_one(self):
        weights = generate_weights(CurveType.BELL, 20)
        assert abs(weights.sum() - 1.0) < 1e-10

    def test_bell_peaks_in_middle(self):
        weights = generate_weights(CurveType.BELL, 20)
        mid = len(weights) // 2
        assert weights[mid] > weights[0]
        assert weights[mid] > weights[-1]

    def test_front_loaded_heavier_early(self):
        weights = generate_weights(CurveType.FRONT_LOADED, 20)
        assert abs(weights.sum() - 1.0) < 1e-10
        first_half = weights[:10].sum()
        second_half = weights[10:].sum()
        assert first_half > second_half

    def test_back_loaded_heavier_late(self):
        weights = generate_weights(CurveType.BACK_LOADED, 20)
        assert abs(weights.sum() - 1.0) < 1e-10
        first_half = weights[:10].sum()
        second_half = weights[10:].sum()
        assert second_half > first_half

    def test_s_curve_sum_to_one(self):
        weights = generate_weights(CurveType.S_CURVE, 20)
        assert abs(weights.sum() - 1.0) < 1e-10

    def test_empty_weeks(self):
        weights = generate_weights(CurveType.FLAT, 0)
        assert len(weights) == 0

    def test_single_week(self):
        weights = generate_weights(CurveType.BELL, 1)
        assert len(weights) == 1
        assert weights[0] == 1.0


class TestShootProportionalWeights:
    def test_proportional_to_days(self):
        weights = generate_shoot_proportional_weights([5, 3, 5, 2])
        assert abs(weights.sum() - 1.0) < 1e-10
        assert weights[0] == weights[2]  # Both 5-day weeks
        assert weights[0] > weights[1]   # 5 > 3
        assert weights[1] > weights[3]   # 3 > 2

    def test_all_zero_days(self):
        weights = generate_shoot_proportional_weights([0, 0, 0])
        assert abs(weights.sum() - 1.0) < 1e-10


class TestMilestoneWeights:
    def test_single_milestone(self):
        weights = generate_milestone_weights(10, [5])
        assert weights[5] == 1.0
        assert weights.sum() == 1.0

    def test_multiple_milestones_even_split(self):
        weights = generate_milestone_weights(10, [2, 7])
        assert abs(weights[2] - 0.5) < 1e-10
        assert abs(weights[7] - 0.5) < 1e-10

    def test_milestone_with_amounts(self):
        weights = generate_milestone_weights(10, [2, 7], [30000, 70000])
        assert abs(weights[2] - 0.3) < 1e-10
        assert abs(weights[7] - 0.7) < 1e-10

    def test_no_milestones_defaults_to_last(self):
        weights = generate_milestone_weights(5, [])
        assert weights[-1] == 1.0
