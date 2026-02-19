from datetime import date, timedelta

import pytest

from app.models.budget import BudgetCategory, BudgetLineItem, ParsedBudget
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


def test_cashflow_grand_total_exact_to_budget(sample_budget, sample_params):
    output = generate_cashflow(
        budget=sample_budget,
        parameters=sample_params,
        distributions=[],
    )

    assert round(output.grand_total, 2) == round(sample_budget.total_budget, 2)


def test_generate_cashflow_prep_to_delivery_extends_to_true_final_episode_delivery(sample_params):
    params = sample_params.model_copy(update={
        "final_delivery_date": date(2025, 6, 6),  # earlier than actual latest episode delivery in fixture
        "first_payroll_week": date(2025, 1, 6),
    })

    budget = ParsedBudget(
        line_items=[
            BudgetLineItem(
                code="1205",
                description="PRODUCTION MANAGER",
                total=100000,
                category=BudgetCategory.ABOVE_THE_LINE,
            )
        ],
        total_budget=100000,
        source_filename="unit-test.xlsx",
        warnings=[],
    )

    output = generate_cashflow(budget=budget, parameters=params, distributions=[])
    row = output.rows[0]
    nonzero = [i for i, v in enumerate(row.weekly_amounts) if abs(v) > 0.001]

    true_final_delivery = max(ep.delivery_date for ep in params.episode_deliveries)
    true_delivery_idx = next(
        i for i, w in enumerate(output.weeks)
        if w.week_commencing <= true_final_delivery < (w.week_commencing + timedelta(days=7))
    )
    next_payroll_after_true_final = next(
        i for i in range(true_delivery_idx + 1, len(output.weeks))
        if output.weeks[i].is_payroll_week is True
    )

    assert nonzero
    assert max(nonzero) == next_payroll_after_true_final
