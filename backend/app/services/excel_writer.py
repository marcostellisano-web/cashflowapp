"""Generate formatted Excel cashflow workbook from CashflowOutput."""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side, numbers
from openpyxl.utils import get_column_letter

from app.models.cashflow import CashflowOutput
from app.models.production import ProductionParameters

# Style constants
HEADER_FONT = Font(bold=True, size=11)
TITLE_FONT = Font(bold=True, size=14)
SUBTITLE_FONT = Font(bold=True, size=10, color="666666")
CURRENCY_FORMAT = '#,##0'
CURRENCY_FORMAT_TOTAL = '#,##0'
THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)

# Phase colors
PHASE_COLORS = {
    "PREP": PatternFill(start_color="B3D9FF", end_color="B3D9FF", fill_type="solid"),       # Light blue
    "SHOOT": PatternFill(start_color="B3FFB3", end_color="B3FFB3", fill_type="solid"),      # Light green
    "WRAP": PatternFill(start_color="FFFFB3", end_color="FFFFB3", fill_type="solid"),       # Light yellow
    "POST": PatternFill(start_color="FFD9B3", end_color="FFD9B3", fill_type="solid"),       # Light orange
    "HIATUS": PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid"),     # Light gray
    "DELIVERY": PatternFill(start_color="FFB3B3", end_color="FFB3B3", fill_type="solid"),   # Light red
}
TOTAL_FILL = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")       # Steel blue
NONZERO_FILL = PatternFill(start_color="F2F7F2", end_color="F2F7F2", fill_type="solid")     # Very light green

DATA_START_ROW = 6
CODE_COL = 1
DESC_COL = 2
TOTAL_COL = 3
FIRST_WEEK_COL = 4


def _get_phase_fill(label: str) -> PatternFill:
    """Return the fill color for a given phase label."""
    upper = label.upper()
    for key, fill in PHASE_COLORS.items():
        if key in upper:
            return fill
    return PatternFill()  # No fill


def _write_main_sheet(wb: Workbook, output: CashflowOutput, params: ProductionParameters):
    """Write the main Cashflow sheet."""
    ws = wb.active
    ws.title = "Cashflow"

    num_weeks = len(output.weeks)
    last_week_col = FIRST_WEEK_COL + num_weeks - 1

    # Row 1: Title
    ws.cell(row=1, column=1, value=f"{output.title} - Cashflow Forecast").font = TITLE_FONT

    # Row 2: Metadata
    series_text = f"Series {params.series_number}" if params.series_number else ""
    ep_text = f"{params.episode_count} Episodes"
    meta = " | ".join(filter(None, [series_text, ep_text]))
    ws.cell(row=2, column=1, value=meta).font = SUBTITLE_FONT

    # Row 4: Phase labels
    for i, week in enumerate(output.weeks):
        col = FIRST_WEEK_COL + i
        cell = ws.cell(row=4, column=col, value=week.phase_label)
        cell.font = Font(bold=True, size=8)
        cell.fill = _get_phase_fill(week.phase_label)
        cell.alignment = Alignment(horizontal="center", text_rotation=90)
        cell.border = THIN_BORDER

    # Row 5: Week headers (week commencing dates)
    ws.cell(row=5, column=CODE_COL, value="Code").font = HEADER_FONT
    ws.cell(row=5, column=DESC_COL, value="Description").font = HEADER_FONT
    ws.cell(row=5, column=TOTAL_COL, value="Total").font = HEADER_FONT
    ws.cell(row=5, column=CODE_COL).border = THIN_BORDER
    ws.cell(row=5, column=DESC_COL).border = THIN_BORDER
    ws.cell(row=5, column=TOTAL_COL).border = THIN_BORDER

    for i, week in enumerate(output.weeks):
        col = FIRST_WEEK_COL + i
        cell = ws.cell(row=5, column=col, value=week.week_commencing)
        cell.font = Font(bold=True, size=8)
        cell.number_format = "DD/MM"
        cell.alignment = Alignment(horizontal="center")
        cell.border = THIN_BORDER

    # Data rows
    for row_idx, row_data in enumerate(output.rows):
        excel_row = DATA_START_ROW + row_idx

        ws.cell(row=excel_row, column=CODE_COL, value=row_data.code).border = THIN_BORDER
        ws.cell(row=excel_row, column=DESC_COL, value=row_data.description).border = THIN_BORDER

        # Total column with SUM formula
        first_data_col_letter = get_column_letter(FIRST_WEEK_COL)
        last_data_col_letter = get_column_letter(last_week_col)
        total_cell = ws.cell(
            row=excel_row,
            column=TOTAL_COL,
            value=f"=SUM({first_data_col_letter}{excel_row}:{last_data_col_letter}{excel_row})",
        )
        total_cell.number_format = CURRENCY_FORMAT
        total_cell.font = Font(bold=True)
        total_cell.border = THIN_BORDER

        # Weekly amounts
        for col_offset, amount in enumerate(row_data.weekly_amounts):
            col = FIRST_WEEK_COL + col_offset
            cell = ws.cell(row=excel_row, column=col, value=round(amount, 2) if amount else 0)
            cell.number_format = CURRENCY_FORMAT
            cell.border = THIN_BORDER
            if amount and amount > 0:
                cell.fill = NONZERO_FILL

    # Weekly totals row
    totals_row = DATA_START_ROW + len(output.rows)
    ws.cell(row=totals_row, column=DESC_COL, value="WEEKLY TOTAL").font = Font(bold=True, size=11)
    ws.cell(row=totals_row, column=DESC_COL).border = THIN_BORDER

    for i in range(num_weeks):
        col = FIRST_WEEK_COL + i
        col_letter = get_column_letter(col)
        cell = ws.cell(
            row=totals_row,
            column=col,
            value=f"=SUM({col_letter}{DATA_START_ROW}:{col_letter}{totals_row - 1})",
        )
        cell.number_format = CURRENCY_FORMAT_TOTAL
        cell.font = Font(bold=True)
        cell.fill = TOTAL_FILL
        cell.border = THIN_BORDER

    # Grand total for totals row
    first_data_col_letter = get_column_letter(FIRST_WEEK_COL)
    last_data_col_letter = get_column_letter(last_week_col)
    grand_total_cell = ws.cell(
        row=totals_row,
        column=TOTAL_COL,
        value=f"=SUM({first_data_col_letter}{totals_row}:{last_data_col_letter}{totals_row})",
    )
    grand_total_cell.number_format = CURRENCY_FORMAT_TOTAL
    grand_total_cell.font = Font(bold=True)
    grand_total_cell.fill = TOTAL_FILL
    grand_total_cell.border = THIN_BORDER

    # Cumulative totals row
    cum_row = totals_row + 1
    ws.cell(row=cum_row, column=DESC_COL, value="CUMULATIVE TOTAL").font = Font(bold=True, size=11)
    ws.cell(row=cum_row, column=DESC_COL).border = THIN_BORDER

    for i in range(num_weeks):
        col = FIRST_WEEK_COL + i
        if i == 0:
            col_letter = get_column_letter(col)
            cell = ws.cell(
                row=cum_row, column=col, value=f"={col_letter}{totals_row}"
            )
        else:
            prev_col_letter = get_column_letter(col - 1)
            col_letter = get_column_letter(col)
            cell = ws.cell(
                row=cum_row,
                column=col,
                value=f"={prev_col_letter}{cum_row}+{col_letter}{totals_row}",
            )
        cell.number_format = CURRENCY_FORMAT_TOTAL
        cell.font = Font(bold=True, italic=True)
        cell.border = THIN_BORDER

    # Column widths
    ws.column_dimensions[get_column_letter(CODE_COL)].width = 10
    ws.column_dimensions[get_column_letter(DESC_COL)].width = 35
    ws.column_dimensions[get_column_letter(TOTAL_COL)].width = 15
    for i in range(num_weeks):
        ws.column_dimensions[get_column_letter(FIRST_WEEK_COL + i)].width = 12

    # Freeze panes: fix code/desc/total columns and header rows
    ws.freeze_panes = ws.cell(row=DATA_START_ROW, column=FIRST_WEEK_COL)


def _write_summary_sheet(wb: Workbook, output: CashflowOutput, params: ProductionParameters):
    """Write the Summary sheet with phase and monthly totals."""
    ws = wb.create_sheet("Summary")

    ws.cell(row=1, column=1, value="Cashflow Summary").font = TITLE_FONT

    # Phase totals
    ws.cell(row=3, column=1, value="Phase Totals").font = HEADER_FONT
    ws.cell(row=4, column=1, value="Phase").font = Font(bold=True)
    ws.cell(row=4, column=2, value="Total").font = Font(bold=True)

    phase_totals: dict[str, float] = {}
    for i, week in enumerate(output.weeks):
        label = week.phase_label
        # Simplify label for grouping
        if "SHOOT" in label.upper():
            group = "PRODUCTION"
        elif "WRAP" in label.upper():
            group = "WRAP"
        elif "POST" in label.upper():
            group = "POST-PRODUCTION"
        elif "PREP" in label.upper():
            group = "PRE-PRODUCTION"
        elif "HIATUS" in label.upper():
            group = "HIATUS"
        else:
            group = label
        phase_totals[group] = phase_totals.get(group, 0) + output.weekly_totals[i]

    row = 5
    for phase, total in phase_totals.items():
        ws.cell(row=row, column=1, value=phase)
        cell = ws.cell(row=row, column=2, value=round(total, 2))
        cell.number_format = CURRENCY_FORMAT
        row += 1

    # Monthly totals
    row += 2
    ws.cell(row=row, column=1, value="Monthly Totals").font = HEADER_FONT
    row += 1
    ws.cell(row=row, column=1, value="Month").font = Font(bold=True)
    ws.cell(row=row, column=2, value="Total").font = Font(bold=True)
    row += 1

    monthly: dict[str, float] = {}
    for i, week in enumerate(output.weeks):
        month_key = week.week_commencing.strftime("%Y-%m")
        monthly[month_key] = monthly.get(month_key, 0) + output.weekly_totals[i]

    for month, total in monthly.items():
        ws.cell(row=row, column=1, value=month)
        cell = ws.cell(row=row, column=2, value=round(total, 2))
        cell.number_format = CURRENCY_FORMAT
        row += 1

    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 18


def _write_parameters_sheet(wb: Workbook, params: ProductionParameters):
    """Write the Parameters sheet documenting the production schedule."""
    ws = wb.create_sheet("Parameters")

    ws.cell(row=1, column=1, value="Production Parameters").font = TITLE_FONT

    row = 3
    fields = [
        ("Title", params.title),
        ("Series Number", params.series_number or "N/A"),
        ("Episode Count", params.episode_count),
        ("Prep Start", params.prep_start.isoformat()),
        ("PP Start", params.pp_start.isoformat()),
        ("PP End", params.pp_end.isoformat()),
        ("Edit Start", params.edit_start.isoformat()),
        ("Final Delivery", params.final_delivery_date.isoformat()),
    ]

    for label, value in fields:
        ws.cell(row=row, column=1, value=label).font = Font(bold=True)
        ws.cell(row=row, column=2, value=str(value))
        row += 1

    # Shooting blocks
    row += 1
    ws.cell(row=row, column=1, value="Shooting Blocks").font = HEADER_FONT
    row += 1
    ws.cell(row=row, column=1, value="Block").font = Font(bold=True)
    ws.cell(row=row, column=2, value="Type").font = Font(bold=True)
    ws.cell(row=row, column=3, value="Episodes").font = Font(bold=True)
    ws.cell(row=row, column=4, value="Start").font = Font(bold=True)
    ws.cell(row=row, column=5, value="End").font = Font(bold=True)
    row += 1

    for block in params.shooting_blocks:
        ws.cell(row=row, column=1, value=block.block_number)
        ws.cell(row=row, column=2, value=block.block_type or "Shoot")
        ws.cell(row=row, column=3, value=", ".join(str(e) for e in block.episode_numbers))
        ws.cell(row=row, column=4, value=block.shoot_start.isoformat())
        ws.cell(row=row, column=5, value=block.shoot_end.isoformat())
        row += 1

    # Episode deliveries
    row += 1
    ws.cell(row=row, column=1, value="Episode Deliveries").font = HEADER_FONT
    row += 1
    headers = ["Episode", "Picture Lock", "Online", "Mix", "Delivery"]
    for i, h in enumerate(headers):
        ws.cell(row=row, column=i + 1, value=h).font = Font(bold=True)
    row += 1

    for ep in params.episode_deliveries:
        ws.cell(row=row, column=1, value=ep.episode_number)
        ws.cell(row=row, column=2, value=ep.picture_lock_date.isoformat() if ep.picture_lock_date else "")
        ws.cell(row=row, column=3, value=ep.online_date.isoformat() if ep.online_date else "")
        ws.cell(row=row, column=4, value=ep.mix_date.isoformat() if ep.mix_date else "")
        ws.cell(row=row, column=5, value=ep.delivery_date.isoformat())
        row += 1

    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 15
    ws.column_dimensions["E"].width = 15
    ws.column_dimensions["F"].width = 15


def write_cashflow_excel(output: CashflowOutput, params: ProductionParameters) -> BytesIO:
    """Generate a complete cashflow Excel workbook.

    Returns a BytesIO buffer containing the .xlsx file.
    """
    wb = Workbook()

    _write_main_sheet(wb, output, params)
    _write_summary_sheet(wb, output, params)
    _write_parameters_sheet(wb, params)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
