"""Formula-based cashflow Excel workbook generator.

Generates the same six-sheet workbook as excel_writer.py, but the budget
line-item weekly amounts are written as Excel IF formulas instead of
pre-computed values.  Each row also gets a visible 'Spread' column showing
which production phase drives the distribution (e.g. SHOOT, PREP, ALL).

The budget total in column C is written as an editable value; changing it
causes every weekly cell in that row to recalculate automatically.

All other sheets (Summary CF, Monthly CF, Vertical CF, Summary, Parameters)
are generated identically to the standard writer and cross-reference the
formula-driven Cashflow sheet correctly.
"""

from io import BytesIO

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

from app.models.budget import ParsedBudget
from app.models.cashflow import CashflowOutput
from app.models.distribution import LineItemDistribution, PhaseAssignment
from app.models.production import ProductionParameters
from app.services.excel_writer import (
    CURRENCY_FORMAT,
    DATA_START_ROW,
    FIRST_WEEK_COL,
    THIN_BORDER,
    TOTAL_COL,
    write_cashflow_excel,
)

_PHASE_SPREAD_LABELS: dict[PhaseAssignment, str] = {
    PhaseAssignment.PREP: "PREP",
    PhaseAssignment.PRODUCTION: "SHOOT",
    PhaseAssignment.POST: "POST",
    PhaseAssignment.DELIVERY: "DELIVERY",
    PhaseAssignment.FULL_SPAN: "ALL",
    PhaseAssignment.PREP_AND_PRODUCTION: "PREP+SHOOT",
    PhaseAssignment.PRODUCTION_AND_POST: "SHOOT+POST",
}


def _week_formula(
    spread: str,
    excel_row: int,
    week_col_letter: str,
    total_col_letter: str,
    phase_range: str,
) -> str:
    """Return the Excel IF formula for one weekly distribution cell.

    Wraps in IFERROR so a phase with zero matching weeks shows 0 rather
    than a #DIV/0! error.
    """
    total_ref = f"${total_col_letter}{excel_row}"
    week_phase = f"{week_col_letter}$4"

    if spread == "ALL":
        count = f'COUNTIF({phase_range},"<>HIATUS")'
        inner = f'IF({week_phase}<>"HIATUS",{total_ref}/{count},0)'
    elif "+" in spread:
        phases = spread.split("+")
        cond = ",".join(f'{week_phase}="{p}"' for p in phases)
        count = "+".join(f'COUNTIF({phase_range},"{p}")' for p in phases)
        inner = f'IF(OR({cond}),{total_ref}/({count}),0)'
    else:
        count = f'COUNTIF({phase_range},"{spread}")'
        inner = f'IF({week_phase}="{spread}",{total_ref}/{count},0)'

    return f"=IFERROR({inner},0)"


def write_formula_cashflow_excel(
    output: CashflowOutput,
    params: ProductionParameters,
    distributions: list[LineItemDistribution],
    budget: ParsedBudget | None = None,
) -> BytesIO:
    """Generate a cashflow workbook where weekly amounts are Excel IF formulas.

    Builds on top of the standard writer: generates the full workbook first,
    then rewrites the Cashflow sheet's data rows to use formulas and adds a
    visible Spread column.
    """
    standard_buf = write_cashflow_excel(output, params, budget=budget)
    wb = load_workbook(standard_buf)
    ws = wb["Cashflow"]

    dist_by_code: dict[str, str] = {
        d.budget_code: _PHASE_SPREAD_LABELS.get(d.phase, "SHOOT")
        for d in distributions
    }

    num_weeks = len(output.weeks)
    last_week_col = FIRST_WEEK_COL + num_weeks - 1
    first_data_col_letter = get_column_letter(FIRST_WEEK_COL)
    last_data_col_letter = get_column_letter(last_week_col)
    total_col_letter = get_column_letter(TOTAL_COL)
    phase_range = f"${first_data_col_letter}$4:${last_data_col_letter}$4"

    # Spread column sits one after the existing summary-code helper column
    # (summary_code_col = FIRST_WEEK_COL + num_weeks + 2, so spread = +3)
    spread_col = FIRST_WEEK_COL + num_weeks + 3
    spread_col_letter = get_column_letter(spread_col)

    # Row 5: rename "Total" → "Budget" to signal it's an editable input,
    # and add the Spread column header
    total_hdr = ws.cell(row=5, column=TOTAL_COL)
    total_hdr.value = "Budget"

    spread_hdr = ws.cell(row=5, column=spread_col, value="Spread")
    spread_hdr.font = Font(name="Calibri", bold=True, size=8, color="555555")
    spread_hdr.alignment = Alignment(horizontal="center")
    spread_hdr.border = THIN_BORDER

    # Rewrite data rows
    for row_idx, row_data in enumerate(output.rows):
        excel_row = DATA_START_ROW + row_idx
        spread = dist_by_code.get(row_data.code, "SHOOT")

        # Replace the SUM formula in TOTAL_COL with the budget amount as a
        # plain value.  The weekly IF formulas below reference this cell, so
        # the SUM would create a circular reference if left as a formula.
        total_cell = ws.cell(row=excel_row, column=TOTAL_COL)
        total_cell.value = round(row_data.total, 2)
        total_cell.number_format = CURRENCY_FORMAT
        total_cell.font = Font(name="Calibri", size=10, bold=True)

        # Weekly cells: replace pre-computed values with IF formulas
        for col_offset in range(num_weeks):
            col = FIRST_WEEK_COL + col_offset
            week_col_letter = get_column_letter(col)
            formula = _week_formula(
                spread, excel_row, week_col_letter, total_col_letter, phase_range
            )
            cell = ws.cell(row=excel_row, column=col)
            cell.value = formula
            cell.number_format = CURRENCY_FORMAT

        # Spread label column
        spread_cell = ws.cell(row=excel_row, column=spread_col, value=spread)
        spread_cell.font = Font(name="Calibri", size=8, color="555555", italic=True)
        spread_cell.alignment = Alignment(horizontal="center")
        spread_cell.border = THIN_BORDER

    ws.column_dimensions[spread_col_letter].width = 10

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
