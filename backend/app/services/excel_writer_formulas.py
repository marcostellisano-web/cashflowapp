"""Formula-based cashflow Excel workbook generator.

Produces the standard six-sheet workbook plus a seventh sheet, "Timing",
that contains one editable row per distribution category (e.g. SHOOT,
PREP, ALL, PREP+SHOOT).  Each row shows a 0/1 pattern across every week
column — 1 means the cost is active that week, 0 means it is not.

The Cashflow sheet's budget-line weekly cells are then formula-driven:

    =IFERROR( $C{row} * Timing!{col}${pattern_row}
              / SUM(Timing!$D${pattern_row}:${last}${pattern_row}), 0 )

Changing any 0→1 or 1→0 in the Timing sheet immediately redistributes
every cost that uses that pattern.  Changing the Budget value in column C
of a Cashflow data row immediately rescales all weekly amounts for that row.

All other derived sheets (Summary CF, Monthly CF, etc.) reference the
formula-driven Cashflow cells and continue to work unchanged.
"""

from io import BytesIO

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.models.budget import ParsedBudget
from app.models.cashflow import CashflowOutput
from app.models.distribution import LineItemDistribution, PhaseAssignment
from app.models.production import ProductionParameters
from app.services.excel_writer import (
    CURRENCY_FORMAT,
    DATA_START_ROW,
    FIRST_WEEK_COL,
    HEADER_FONT,
    THIN_BORDER,
    TITLE_FONT,
    TOTAL_COL,
    _get_phase_fill,
    write_cashflow_excel,
)

# ── Phase → Timing label mapping ─────────────────────────────────────────────

_PHASE_SPREAD_LABELS: dict[PhaseAssignment, str] = {
    PhaseAssignment.PREP: "PREP",
    PhaseAssignment.PRODUCTION: "SHOOT",
    PhaseAssignment.POST: "POST",
    PhaseAssignment.DELIVERY: "DELIVERY",
    PhaseAssignment.FULL_SPAN: "ALL",
    PhaseAssignment.PREP_AND_PRODUCTION: "PREP+SHOOT",
    PhaseAssignment.PRODUCTION_AND_POST: "SHOOT+POST",
}

_SPREAD_DESCRIPTIONS: dict[str, str] = {
    "PREP": "Prep weeks only — equal split",
    "SHOOT": "Shoot weeks only — equal split",
    "POST": "Post weeks only — equal split",
    "WRAP": "Wrap weeks only — equal split",
    "DELIVERY": "Delivery weeks only — equal split",
    "ALL": "All active weeks (excludes hiatus) — equal split",
    "PREP+SHOOT": "Prep and Shoot weeks — equal split",
    "SHOOT+POST": "Shoot and Post weeks — equal split",
}

# Timing sheet layout constants (column positions match the Cashflow sheet
# so cross-sheet references use the same column letters).
_TIMING_SHEET = "Timing"
_TIMING_DATA_START = DATA_START_ROW  # pattern rows start at row 6, same as Cashflow

# Fill for the editable pattern cells (subtle yellow)
_PATTERN_FILL = PatternFill(start_color="FFFDE7", end_color="FFFDE7", fill_type="solid")
_ACTIVE_FILL = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")
_HEADER_FILL = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")


def _timing_value(spread: str, phase_label: str) -> int:
    """Return 1 if this week is active for the given spread, 0 otherwise."""
    phase = phase_label.upper()
    if spread == "SHOOT":
        return 1 if "SHOOT" in phase else 0
    if spread == "PREP":
        return 1 if "PREP" in phase else 0
    if spread == "POST":
        return 1 if "POST" in phase else 0
    if spread == "WRAP":
        return 1 if "WRAP" in phase else 0
    if spread == "DELIVERY":
        return 1 if "DELIVERY" in phase else 0
    if spread == "ALL":
        return 0 if "HIATUS" in phase else 1
    if spread == "PREP+SHOOT":
        return 1 if ("PREP" in phase or "SHOOT" in phase) else 0
    if spread == "SHOOT+POST":
        return 1 if ("SHOOT" in phase or "POST" in phase) else 0
    # Fallback: everything except hiatus
    return 0 if "HIATUS" in phase else 1


def _write_timing_sheet(
    wb,
    output: CashflowOutput,
    spread_to_row: dict[str, int],
) -> None:
    """Create the 'Timing' sheet with one editable pattern row per spread type."""
    ws = wb.create_sheet(_TIMING_SHEET, 1)  # insert right after Cashflow

    num_weeks = len(output.weeks)
    last_week_col = FIRST_WEEK_COL + num_weeks - 1

    # ── Row 1: title ─────────────────────────────────────────────────────────
    ws.cell(row=1, column=1, value="Distribution Timing Patterns").font = TITLE_FONT

    # ── Row 2: instructions ──────────────────────────────────────────────────
    instr = ws.cell(
        row=2,
        column=1,
        value=(
            "Edit 0 / 1 values in the week columns below to change when a cost is "
            "distributed.  Each Cashflow row multiplies its Budget by the pattern "
            "weight and divides by the sum of weights for that row."
        ),
    )
    instr.font = Font(name="Calibri", italic=True, size=9, color="555555")

    # ── Row 3: column headers ────────────────────────────────────────────────
    hdr_label = ws.cell(row=3, column=1, value="Pattern")
    hdr_label.font = HEADER_FONT
    hdr_label.fill = _HEADER_FILL
    hdr_label.border = THIN_BORDER

    hdr_desc = ws.cell(row=3, column=2, value="Description")
    hdr_desc.font = HEADER_FONT
    hdr_desc.fill = _HEADER_FILL
    hdr_desc.border = THIN_BORDER

    for i in range(num_weeks):
        col = FIRST_WEEK_COL + i
        col_letter = get_column_letter(col)
        # Phase label — linked live from the Cashflow sheet
        phase_cell = ws.cell(row=3, column=col, value=f"=Cashflow!{col_letter}4")
        phase_cell.font = Font(name="Calibri", bold=True, size=8)
        phase_cell.fill = _HEADER_FILL
        phase_cell.alignment = Alignment(horizontal="center", text_rotation=90)
        phase_cell.border = THIN_BORDER

    # ── Row 4: week dates ────────────────────────────────────────────────────
    ws.cell(row=4, column=1, value="Week commencing →").font = Font(
        name="Calibri", italic=True, size=8, color="888888"
    )
    for i in range(num_weeks):
        col = FIRST_WEEK_COL + i
        col_letter = get_column_letter(col)
        date_cell = ws.cell(row=4, column=col, value=f"=Cashflow!{col_letter}5")
        date_cell.font = Font(name="Calibri", size=7)
        date_cell.number_format = "DD-MMM"
        date_cell.alignment = Alignment(horizontal="center")
        date_cell.border = THIN_BORDER

    # ── Pattern rows ─────────────────────────────────────────────────────────
    for spread, excel_row in spread_to_row.items():
        label_cell = ws.cell(row=excel_row, column=1, value=spread)
        label_cell.font = Font(name="Calibri", bold=True, size=10)
        label_cell.border = THIN_BORDER

        desc_cell = ws.cell(
            row=excel_row,
            column=2,
            value=_SPREAD_DESCRIPTIONS.get(spread, spread),
        )
        desc_cell.font = Font(name="Calibri", size=9, italic=True, color="555555")
        desc_cell.border = THIN_BORDER

        for i, week in enumerate(output.weeks):
            col = FIRST_WEEK_COL + i
            val = _timing_value(spread, week.phase_label)
            cell = ws.cell(row=excel_row, column=col, value=val)
            cell.number_format = "0"
            cell.alignment = Alignment(horizontal="center")
            cell.border = THIN_BORDER
            cell.fill = _ACTIVE_FILL if val else _PATTERN_FILL
            cell.font = Font(
                name="Calibri",
                bold=bool(val),
                size=9,
                color="1B5E20" if val else "BBBBBB",
            )

    # ── Column widths ─────────────────────────────────────────────────────────
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 40
    for i in range(num_weeks):
        ws.column_dimensions[get_column_letter(FIRST_WEEK_COL + i)].width = 6

    ws.freeze_panes = ws.cell(row=5, column=FIRST_WEEK_COL)


def write_formula_cashflow_excel(
    output: CashflowOutput,
    params: ProductionParameters,
    distributions: list[LineItemDistribution],
    budget: ParsedBudget | None = None,
) -> BytesIO:
    """Generate a formula-based cashflow workbook with an editable Timing sheet.

    Steps:
    1. Generate the full standard workbook (all sheets, all styling).
    2. Insert a new 'Timing' sheet listing one editable 0/1 pattern row per
       unique spread category.
    3. Rewrite the Cashflow sheet data rows so each weekly cell references
       its pattern row in the Timing sheet.
    4. Rename the 'Budget' column header to signal it's an editable input.
    """
    # ── Step 1: standard workbook ─────────────────────────────────────────────
    standard_buf = write_cashflow_excel(output, params, budget=budget)
    wb = load_workbook(standard_buf)
    ws = wb["Cashflow"]

    # ── Step 2: build spread → pattern row mapping ────────────────────────────
    dist_by_code: dict[str, str] = {
        d.budget_code: _PHASE_SPREAD_LABELS.get(d.phase, "SHOOT")
        for d in distributions
    }

    # Preserve insertion order so the Timing sheet rows appear in the order
    # the spreads are first encountered in the cashflow.
    seen: dict[str, int] = {}
    for row_data in output.rows:
        spread = dist_by_code.get(row_data.code, "SHOOT")
        if spread not in seen:
            seen[spread] = _TIMING_DATA_START + len(seen)

    # spread_to_row maps e.g. "SHOOT" → 6, "PREP" → 7, …
    spread_to_row = seen

    # ── Step 3: create Timing sheet ───────────────────────────────────────────
    _write_timing_sheet(wb, output, spread_to_row)

    # ── Step 4: rewrite Cashflow data rows ───────────────────────────────────
    num_weeks = len(output.weeks)
    last_week_col = FIRST_WEEK_COL + num_weeks - 1
    last_week_col_letter = get_column_letter(last_week_col)
    first_data_col_letter = get_column_letter(FIRST_WEEK_COL)

    # Rename "Total" header to "Budget" (it's now an editable input, not a sum)
    ws.cell(row=5, column=TOTAL_COL).value = "Budget"

    # Add a "Pattern" column header after the summary-code helper column
    pattern_col = FIRST_WEEK_COL + num_weeks + 3
    pattern_col_letter = get_column_letter(pattern_col)
    phdr = ws.cell(row=5, column=pattern_col, value="Pattern")
    phdr.font = Font(name="Calibri", bold=True, size=8, color="1565C0")
    phdr.alignment = Alignment(horizontal="center")
    phdr.border = THIN_BORDER

    for row_idx, row_data in enumerate(output.rows):
        excel_row = DATA_START_ROW + row_idx
        spread = dist_by_code.get(row_data.code, "SHOOT")
        prow = spread_to_row[spread]  # row number in the Timing sheet

        # Column C: write budget total as a plain value.
        # The weekly formulas reference $C{row}, so leaving a SUM formula here
        # would create a circular reference.
        total_cell = ws.cell(row=excel_row, column=TOTAL_COL)
        total_cell.value = round(row_data.total, 2)
        total_cell.number_format = CURRENCY_FORMAT
        total_cell.font = Font(name="Calibri", size=10, bold=True)

        # Weekly columns: formula referencing the Timing sheet pattern row.
        #   = IFERROR( Budget × weight_this_week / sum_of_weights , 0 )
        sum_range = f"{_TIMING_SHEET}!${first_data_col_letter}${prow}:${last_week_col_letter}${prow}"
        for col_offset in range(num_weeks):
            col = FIRST_WEEK_COL + col_offset
            wcol = get_column_letter(col)
            weight_ref = f"{_TIMING_SHEET}!{wcol}${prow}"
            formula = (
                f"=IFERROR($C{excel_row}*{weight_ref}"
                f"/SUM({sum_range}),0)"
            )
            cell = ws.cell(row=excel_row, column=col)
            cell.value = formula
            cell.number_format = CURRENCY_FORMAT

        # Pattern column: shows which Timing row drives this line
        pc = ws.cell(row=excel_row, column=pattern_col, value=spread)
        pc.font = Font(name="Calibri", size=8, color="1565C0", italic=True)
        pc.alignment = Alignment(horizontal="center")
        pc.border = THIN_BORDER

    ws.column_dimensions[pattern_col_letter].width = 12

    # ── Step 5: save ──────────────────────────────────────────────────────────
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
