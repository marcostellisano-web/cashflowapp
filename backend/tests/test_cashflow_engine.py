import pytest

from app.services.cashflow_engine import generate_cashflow


def test_generate_cashflow_produces_output(sample_budget, sample_params):
    output = generate_cashflow(
        budget=sample_budget,
        parameters=sample_params,
        distributions=[],  # All auto-assigned
    )

    assert output.title == "Test Show"
    assert len(output.rows) == len(sample_budget.line_items)
    assert len(output.weeks) > 0
    assert len(output.weekly_totals) == len(output.weeks)
    assert len(output.cumulative_totals) == len(output.weeks)


def test_cashflow_totals_match_budget(sample_budget, sample_params):
    output = generate_cashflow(
        budget=sample_budget,
        parameters=sample_params,
        distributions=[],
    )

    # Each row's distributed amounts should sum to its total (within rounding)
    for row, item in zip(output.rows, sample_budget.line_items):
        distributed_total = sum(row.weekly_amounts)
        assert abs(distributed_total - item.total) < 1.0, (
            f"{row.code}: distributed {distributed_total} vs budget {item.total}"
        )

    # Grand total should match budget total
    assert abs(output.grand_total - sample_budget.total_budget) < len(output.rows)


def test_cashflow_cumulative_totals_increasing(sample_budget, sample_params):
    output = generate_cashflow(
        budget=sample_budget,
        parameters=sample_params,
        distributions=[],
    )

    for i in range(1, len(output.cumulative_totals)):
        assert output.cumulative_totals[i] >= output.cumulative_totals[i - 1]


def test_cashflow_weekly_totals_sum_correctly(sample_budget, sample_params):
    output = generate_cashflow(
        budget=sample_budget,
        parameters=sample_params,
        distributions=[],
    )

    for week_idx in range(len(output.weeks)):
        column_sum = sum(row.weekly_amounts[week_idx] for row in output.rows)
        assert abs(column_sum - output.weekly_totals[week_idx]) < 0.1
