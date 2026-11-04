from openpyxl import load_workbook

from app.services.cashflow_engine import generate_cashflow
from app.services.excel_writer_formulas import write_formula_cashflow_excel


def _find_row(ws, label):
    for r in range(1, ws.max_row + 1):
        if ws.cell(r, 2).value == label:
            return r
    raise AssertionError(f"{label} row not found")


def test_formula_totals_reference_week_columns(sample_budget, sample_params):
    """Weekly/cumulative totals must point at the week columns (E+), not the
    inserted Pattern column (D)."""
    output = generate_cashflow(
        budget=sample_budget, parameters=sample_params, distributions=[]
    )
    wb = load_workbook(
        write_formula_cashflow_excel(output, sample_params, [], budget=sample_budget)
    )
    ws = wb["Cashflow"]

    totals = _find_row(ws, "WEEKLY TOTAL")
    cum = _find_row(ws, "CUMULATIVE TOTAL")
    last_data = totals - 1

    assert ws.cell(totals, 4).value is None  # Pattern column stays empty
    assert ws.cell(totals, 5).value == f"=SUM(E6:E{last_data})"
    assert ws.cell(totals, 6).value == f"=SUM(F6:F{last_data})"
    assert ws.cell(cum, 5).value == f"=E{totals}"
    assert ws.cell(cum, 6).value == f"=E{cum}+F{totals}"
    assert ws.cell(totals, 3).value.startswith(f"=SUM(E{totals}:")
