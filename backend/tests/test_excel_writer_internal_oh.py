from app.models.budget import BudgetDetailRow, BudgetLineItem, ParsedBudget
from app.models.cashflow import CashflowRow
from app.services.excel_writer import _get_outflow_component_codes


def _make_budget(detail_rows):
    return ParsedBudget(
        line_items=[BudgetLineItem(code='1201', description='Crew', total=1000)],
        total_budget=1000,
        source_filename='test.xlsx',
        warnings=[],
        detail_rows=detail_rows,
    )


def test_internal_oh_counts_total_fringes_when_label_in_description():
    budget = _make_budget([
        BudgetDetailRow(account='1201', description='Line A', subtotal=100, groups='Internal OH'),
        BudgetDetailRow(account='1201', description='Total Fringes', subtotal=25, groups=None),
    ])
    rows = [CashflowRow(code='1201', description='Crew', total=1000, weekly_amounts=[1000])]

    _, internal_oh_amounts = _get_outflow_component_codes(budget, rows)

    assert internal_oh_amounts['1201'] == 125


def test_internal_oh_counts_total_fringes_when_label_in_groups_column():
    budget = _make_budget([
        BudgetDetailRow(account='1201', description='Line A', subtotal=100, groups='Internal OH'),
        BudgetDetailRow(account='1201', description='Fringe Rollup', subtotal=25, groups='Total Fringes'),
    ])
    rows = [CashflowRow(code='1201', description='Crew', total=1000, weekly_amounts=[1000])]

    _, internal_oh_amounts = _get_outflow_component_codes(budget, rows)

    assert internal_oh_amounts['1201'] == 125
