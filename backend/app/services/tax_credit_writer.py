"""Generate a formatted Tax Credit Filing Budget Excel workbook from a ParsedBudget."""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.models.budget import ParsedBudget

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------
CURRENCY_FORMAT = '#,##0'
# Accounting style: no currency symbol, zero shows as " - ", negatives in parens
_ACCOUNTING_FORMAT = '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'

_THIN = Side(style="thin")
_THIN_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
_BOTTOM_BORDER = Border(bottom=_THIN)
_NO_BORDER = Border()

_BLACK_FILL = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
_SECTION_HEADER_FILL = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
_LIGHT_GRAY_FILL = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
_TOTAL_FILL = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
_GRAND_TOTAL_FILL = PatternFill(start_color="000000", end_color="000000", fill_type="solid")

_WHITE_BOLD = Font(bold=True, color="FFFFFF", size=10)
_BOLD = Font(bold=True, size=10)
_NORMAL = Font(size=10)
_TITLE_FONT = Font(bold=True, size=11)
_BOLD_ITALIC = Font(bold=True, italic=True, size=10)

_TITLE_GREEN_FILL = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid")

_CENTER = Alignment(horizontal="center", vertical="center")
_LEFT = Alignment(horizontal="left", vertical="center")
_RIGHT = Alignment(horizontal="right", vertical="center")

# ---------------------------------------------------------------------------
# CAVCO Topsheet account definitions
# ---------------------------------------------------------------------------
# Each entry is one of:
#   ("XX.00", "Category name")          — a data row with an account code
#   ("TOTAL", "label", "section_key")   — a section-total row
#   ("HEADER", "label")                 — a section header label (gray)
#   ("BLANK",)                          — an empty spacer row

TOPSHEET_STRUCTURE: list[tuple] = [
    # Above the line
    ("01.00", "Story rights/Acquisitions"),
    ("02.00", "Script"),
    ("03.00", "Development costs"),
    ("04.00", "Producer(s)"),
    ("05.00", "Director(s)"),
    ("06.00", "Stars"),
    ("TOTAL", 'TOTAL "A" \u2013 ABOVE THE LINE', "A"),
    # Section B
    ("HEADER", '"B" \u2013 PRODUCTION'),
    ("10.00", "Cast"),
    ("11.00", "Background Performers (Extras)"),
    ("12.00", "Production labour"),
    ("13.00", "Production Design/Art Department labour"),
    ("14.00", "Construction labour"),
    ("15.00", "Set Dressing labour"),
    ("16.00", "Props labour"),
    ("17.00", "Special Effects labour"),
    ("18.00", "Animal Wrangling labour"),
    ("19.00", "Wardrobe labour"),
    ("20.00", "Makeup/Hair labour"),
    ("21.00", "Video Technical crew"),
    ("22.00", "Camera labour"),
    ("23.00", "Electrical labour"),
    ("24.00", "Grip labour"),
    ("25.00", "Production Sound labour"),
    ("26.00", "Transportation labour"),
    ("27.00", "Fringe benefits"),
    ("28.00", "Production office expenses"),
    ("29.00", "Studio expenses"),
    ("30.00", "Location office expenses"),
    ("31.00", "Location expenses"),
    ("32.00", "Unit expenses"),
    ("33.00", "Travel & Living expenses"),
    ("34.00", "Transportation"),
    ("35.00", "Construction materials"),
    ("36.00", "Art supplies"),
    ("37.00", "Set dressing"),
    ("38.00", "Props"),
    ("39.00", "Special effects"),
    ("40.00", "Animals"),
    ("41.00", "Wardrobe supplies"),
    ("42.00", "Makeup/Hair supplies"),
    ("43.00", "Videotape studio"),
    ("44.00", "Mobile video unit"),
    ("45.00", "Camera equipment"),
    ("46.00", "Electrical equipment"),
    ("47.00", "Grip equipment"),
    ("48.00", "Sound equipment"),
    ("49.00", "Second unit"),
    ("50.00", "Video stock"),
    ("51.00", "Production laboratory"),
    ("52.00", "Voice recording \u2013 Animation"),
    ("53.00", "Production unit \u2013 Animation"),
    ("54.00", "Art & Design unit \u2013 Animation"),
    ("55.00", "2D Animation unit"),
    ("56.00", "3D Animation unit"),
    ("57.00", "Live Animation (MOCAP) unit"),
    ("58.00", "Fringe benefits \u2013 Animation"),
    ("59.00", "Animation materials & supplies"),
    ("TOTAL", 'TOTAL PRODUCTION "B"', "B"),
    # Section C
    ("HEADER", '"C" \u2013 POST-PRODUCTION'),
    ("60.00", "Post Production - Edit labour"),
    ("61.00", "Editing equipment"),
    ("62.00", "Video post production (picture)"),
    ("63.00", "Video post production (sound)"),
    ("64.00", "Film post production (picture)"),
    ("65.00", "Film post production (sound)"),
    ("66.00", "Music"),
    ("67.00", "Titles/Stock footage/Visual effects"),
    ("68.00", "Versioning"),
    ("69.00", "Amortization (series)"),
    ("TOTAL", 'TOTAL POST-PRODUCTION "C"', "C"),
    ("TOTAL_MULTI", 'TOTAL "B" + "C"\n(PRODUCTION AND POST PRODUCTION)', ("B", "C")),
    # Section D
    ("HEADER", '"D" \u2013 OTHER'),
    ("70.00", "Unit publicity"),
    ("71.00", "General expenses"),
    ("72.00", "Indirect costs"),
    ("TOTAL", 'TOTAL OTHER "D"', "D"),
    ("TOTAL_MULTI", 'TOTAL "A" + "B" + "C" + "D"', ("A", "B", "C", "D")),
    # Final items
    ("80.00", "Contingency"),
    ("81.00", "Completion guarantee"),
    ("GRAND_TOTAL", "GRAND TOTAL"),
]


def _cavco_to_mm_prefix(cavco_code: str) -> str:
    """Convert CAVCO code like '01.00' to 4-char account prefix '0100'."""
    integer_part = cavco_code.split(".")[0]  # "01", "10", "80"
    return integer_part + "00"              # "0100", "1000", "8000"


def _get_account_total(budget: "ParsedBudget", cavco_code: str) -> float:
    """Return the total for a CAVCO account code.

    Prefers pre-aggregated topsheet_totals from the source file's Topsheet tab.
    Falls back to summing matching line items when topsheet_totals is empty.
    """
    prefix = _cavco_to_mm_prefix(cavco_code)
    if budget.topsheet_totals:
        return budget.topsheet_totals.get(prefix, 0.0)
    # Fallback: sum line items whose stripped code starts with the prefix
    total = 0.0
    for item in budget.line_items:
        code = item.code.replace(".", "").replace(" ", "")
        if code.startswith(prefix):
            total += item.total
    return total


def _build_section_totals(budget: "ParsedBudget") -> dict[str, float]:
    """Pre-compute section totals A, B, C, D for the topsheet."""
    section_ranges = {
        "A": [f"{n:02d}.00" for n in range(1, 7)],
        "B": [f"{n:02d}.00" for n in range(10, 60)],
        "C": [f"{n:02d}.00" for n in range(60, 70)],
        "D": [f"{n:02d}.00" for n in range(70, 73)],
    }
    return {
        section: sum(_get_account_total(budget, code) for code in codes)
        for section, codes in section_ranges.items()
    }


# ---------------------------------------------------------------------------
# Topsheet worksheet builder
# ---------------------------------------------------------------------------

def _write_topsheet(ws, budget: ParsedBudget, title: str) -> None:
    ws.title = "Topsheet"

    # Column widths
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 16

    # ── Title row ──────────────────────────────────────────────────────────
    ws.row_dimensions[1].height = 22
    title_cell = ws.cell(row=1, column=1, value="Title")
    title_cell.font = _BOLD
    title_cell.alignment = _LEFT

    value_cell = ws.cell(row=1, column=2, value=title)
    value_cell.font = _TITLE_FONT
    value_cell.alignment = _LEFT
    value_cell.border = _BOTTOM_BORDER

    ws.row_dimensions[2].height = 8  # spacer

    # ── Column headers ─────────────────────────────────────────────────────
    header_row = 3
    ws.row_dimensions[header_row].height = 18
    for col, label in enumerate(["Account", "Category", "Total"], start=1):
        cell = ws.cell(row=header_row, column=col, value=label)
        cell.font = _BOLD
        cell.alignment = _CENTER if col != 2 else _LEFT
        cell.border = _THIN_BORDER

    # ── Pre-compute values ─────────────────────────────────────────────────
    section_totals = _build_section_totals(budget)

    # Grand total = sum of all sections + 80.00 + 81.00
    grand_total = (
        sum(section_totals.values())
        + _get_account_total(budget, "80.00")
        + _get_account_total(budget, "81.00")
    )

    # ── Data rows ──────────────────────────────────────────────────────────
    current_row = header_row + 1

    for entry in TOPSHEET_STRUCTURE:
        kind = entry[0]
        ws.row_dimensions[current_row].height = 16

        if kind == "BLANK":
            current_row += 1
            continue

        elif kind == "HEADER":
            # Gray section header, spans A-C
            label = entry[1]
            ws.merge_cells(
                start_row=current_row, start_column=1,
                end_row=current_row, end_column=3,
            )
            cell = ws.cell(row=current_row, column=1, value=label)
            cell.font = _BOLD
            cell.fill = _SECTION_HEADER_FILL
            cell.alignment = _LEFT
            cell.border = _THIN_BORDER
            current_row += 1

        elif kind == "TOTAL":
            label = entry[1]
            section_key = entry[2]
            amount = section_totals.get(section_key, 0.0)

            # Black row, white bold text
            for col in range(1, 4):
                cell = ws.cell(row=current_row, column=col)
                cell.fill = _BLACK_FILL
                cell.border = _THIN_BORDER
                cell.font = _WHITE_BOLD
                if col == 1:
                    cell.alignment = _LEFT
                elif col == 2:
                    cell.value = label
                    cell.alignment = _LEFT
                else:
                    cell.value = amount
                    cell.number_format = CURRENCY_FORMAT
                    cell.alignment = _RIGHT
            current_row += 1

        elif kind == "TOTAL_MULTI":
            label = entry[1]
            section_keys = entry[2]
            amount = sum(section_totals.get(k, 0.0) for k in section_keys)

            ws.row_dimensions[current_row].height = 28
            for col in range(1, 4):
                cell = ws.cell(row=current_row, column=col)
                cell.fill = _BLACK_FILL
                cell.border = _THIN_BORDER
                cell.font = _WHITE_BOLD
                cell.alignment = Alignment(
                    horizontal="left" if col <= 2 else "right",
                    vertical="center",
                    wrap_text=True,
                )
                if col == 2:
                    cell.value = label
                elif col == 3:
                    cell.value = amount
                    cell.number_format = CURRENCY_FORMAT
                    cell.alignment = Alignment(
                        horizontal="right", vertical="center", wrap_text=True
                    )
            current_row += 1

        elif kind == "GRAND_TOTAL":
            label = entry[1]
            ws.row_dimensions[current_row].height = 18
            for col in range(1, 4):
                cell = ws.cell(row=current_row, column=col)
                cell.fill = _BLACK_FILL
                cell.border = _THIN_BORDER
                cell.font = _WHITE_BOLD
                if col == 2:
                    cell.value = label
                    cell.alignment = _LEFT
                elif col == 3:
                    cell.value = grand_total
                    cell.number_format = CURRENCY_FORMAT
                    cell.alignment = _RIGHT
                else:
                    cell.alignment = _LEFT
            current_row += 1

        else:
            # Regular data row: ("XX.00", "Category name")
            cavco_code = kind
            label = entry[1]
            amount = _get_account_total(budget, cavco_code)

            row_fill = _LIGHT_GRAY_FILL if current_row % 2 == 0 else None

            code_cell = ws.cell(row=current_row, column=1, value=cavco_code)
            code_cell.font = _NORMAL
            code_cell.alignment = _CENTER
            code_cell.border = _THIN_BORDER
            if row_fill:
                code_cell.fill = row_fill

            desc_cell = ws.cell(row=current_row, column=2, value=label)
            desc_cell.font = _NORMAL
            desc_cell.alignment = _LEFT
            desc_cell.border = _THIN_BORDER
            if row_fill:
                desc_cell.fill = row_fill

            amt_cell = ws.cell(row=current_row, column=3, value=amount)
            amt_cell.font = _NORMAL
            amt_cell.number_format = CURRENCY_FORMAT
            amt_cell.alignment = _RIGHT
            amt_cell.border = _THIN_BORDER
            if row_fill:
                amt_cell.fill = row_fill

            current_row += 1

    # Freeze panes below header row
    ws.freeze_panes = "A4"


# ---------------------------------------------------------------------------
# Budget Lines detail worksheet builder
# ---------------------------------------------------------------------------

def _write_budget_lines(ws, budget: ParsedBudget) -> None:
    ws.title = "Budget Lines"

    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 16
    ws.column_dimensions["D"].width = 20

    # Header row
    headers = ["Account Code", "Description", "Total", "CAVCO Category"]
    ws.row_dimensions[1].height = 18
    for col, label in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=label)
        cell.font = _BOLD
        cell.alignment = _CENTER if col != 2 else _LEFT
        cell.border = _THIN_BORDER
        cell.fill = _SECTION_HEADER_FILL

    # Build a lookup: mm_prefix → CAVCO label for tooltip column
    cavco_map: dict[str, str] = {}
    for entry in TOPSHEET_STRUCTURE:
        if len(entry) == 2 and entry[0] not in ("HEADER", "BLANK", "GRAND_TOTAL"):
            cavco_code = entry[0]
            cavco_label = entry[1]
            mm_prefix = _cavco_to_mm_prefix(cavco_code)
            cavco_map[mm_prefix] = f"{cavco_code} {cavco_label}"

    # Sort line items by code
    sorted_items = sorted(budget.line_items, key=lambda x: x.code)

    for row_idx, item in enumerate(sorted_items, start=2):
        ws.row_dimensions[row_idx].height = 15
        row_fill = _LIGHT_GRAY_FILL if row_idx % 2 == 0 else None

        clean_code = item.code.replace(".", "").replace(" ", "")
        # Find matching CAVCO prefix (first 4 chars of clean code)
        cavco_label = ""
        for prefix, label in cavco_map.items():
            if clean_code.startswith(prefix):
                cavco_label = label
                break

        cells_data = [
            (item.code, _CENTER),
            (item.description, _LEFT),
            (item.total, _RIGHT),
            (cavco_label, _LEFT),
        ]
        for col, (value, align) in enumerate(cells_data, start=1):
            cell = ws.cell(row=row_idx, column=col, value=value)
            cell.font = _NORMAL
            cell.alignment = align
            cell.border = _THIN_BORDER
            if row_fill:
                cell.fill = row_fill
            if col == 3:
                cell.number_format = CURRENCY_FORMAT

    # Total row
    total_row = len(sorted_items) + 2
    ws.row_dimensions[total_row].height = 18
    for col in range(1, 5):
        cell = ws.cell(row=total_row, column=col)
        cell.fill = _BLACK_FILL
        cell.border = _THIN_BORDER
        cell.font = _WHITE_BOLD
        if col == 2:
            cell.value = "TOTAL"
            cell.alignment = _LEFT
        elif col == 3:
            cell.value = budget.total_budget
            cell.number_format = CURRENCY_FORMAT
            cell.alignment = _RIGHT
        else:
            cell.alignment = _LEFT

    ws.freeze_panes = "A2"



def _normalize_account_code(code: str) -> str:
    return code.replace(".", "").replace(" ", "").strip()


def _topsheet_prefix_from_account(account: str) -> str:
    clean = _normalize_account_code(account)
    if len(clean) < 2 or not clean[:2].isdigit():
        return ""
    return f"{clean[:2]}00"


def _format_topsheet_code(prefix: str) -> str:
    if len(prefix) == 4 and prefix.isdigit():
        return f"{prefix[:2]}.00"
    return prefix


def _prefix_sort_key(prefix: str) -> tuple[int, str]:
    if prefix.isdigit():
        return (int(prefix), prefix)
    return (9999, prefix)


def _write_detail_budget(ws, budget: ParsedBudget) -> None:
    ws.title = "Detail Budget"

    headers = [
        "Account",
        "Account Description",
        "Description",
        "Amount",
        "Unit",
        "x",
        "Unit 2",
        "Currency",
        "Rate",
        "Unit 3",
        "Subtotal",
    ]

    widths = [12, 34, 40, 10, 10, 6, 10, 10, 12, 10, 14]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width

    for col, label in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=label)
        cell.font = _BOLD
        cell.alignment = _LEFT if col in (1, 2, 3) else _CENTER
        cell.border = _NO_BORDER
        cell.fill = _LIGHT_GRAY_FILL

    for col in range(1, 12):
        top_cell = ws.cell(row=1, column=col)
        top_cell.border = Border(
            left=top_cell.border.left,
            right=top_cell.border.right,
            top=_THIN,
            bottom=_THIN,
        )
    ws.cell(row=1, column=1).border = Border(
        left=_THIN,
        right=ws.cell(row=1, column=1).border.right,
        top=ws.cell(row=1, column=1).border.top,
        bottom=ws.cell(row=1, column=1).border.bottom,
    )
    ws.cell(row=1, column=11).border = Border(
        left=ws.cell(row=1, column=11).border.left,
        right=_THIN,
        top=ws.cell(row=1, column=11).border.top,
        bottom=ws.cell(row=1, column=11).border.bottom,
    )

    category_by_account: dict[str, str] = {}
    for item in budget.line_items:
        category_by_account[_normalize_account_code(item.code)] = item.description

    detail_rows = [r for r in budget.detail_rows if r.subtotal > 0]

    topsheet_name_by_prefix = {
        _cavco_to_mm_prefix(entry[0]): entry[1]
        for entry in TOPSHEET_STRUCTURE
        if len(entry) == 2 and entry[0] not in ("HEADER", "BLANK", "GRAND_TOTAL")
    }

    grouped: dict[str, list] = {}
    for row in detail_rows:
        prefix = _topsheet_prefix_from_account(row.account)
        if not prefix:
            continue
        grouped.setdefault(prefix, []).append(row)

    def _set_outline_border(start_row: int, end_row: int) -> None:
        for col in range(1, 12):
            top_cell = ws.cell(row=start_row, column=col)
            top_cell.border = Border(
                left=top_cell.border.left,
                right=top_cell.border.right,
                top=_THIN,
                bottom=top_cell.border.bottom,
            )
            bottom_cell = ws.cell(row=end_row, column=col)
            bottom_cell.border = Border(
                left=bottom_cell.border.left,
                right=bottom_cell.border.right,
                top=bottom_cell.border.top,
                bottom=_THIN,
            )
        for row in range(start_row, end_row + 1):
            left_cell = ws.cell(row=row, column=1)
            left_cell.border = Border(
                left=_THIN,
                right=left_cell.border.right,
                top=left_cell.border.top,
                bottom=left_cell.border.bottom,
            )
            right_cell = ws.cell(row=row, column=11)
            right_cell.border = Border(
                left=right_cell.border.left,
                right=_THIN,
                top=right_cell.border.top,
                bottom=right_cell.border.bottom,
            )

    row_idx = 2
    section_total_rows_by_prefix: dict[str, int] = {}

    section_group_end_prefixes = {
        "A": 600,
        "B": 5900,
        "C": 6900,
        "D": 7200,
    }
    group_labels = {
        "A": 'TOTAL "A" – ABOVE THE LINE',
        "B": 'TOTAL PRODUCTION "B"',
        "C": 'TOTAL POST-PRODUCTION "C"',
        "D": 'TOTAL OTHER "D"',
    }
    emitted_groups: set[str] = set()

    def _emit_group_total(group_key: str) -> None:
        nonlocal row_idx
        if group_key in emitted_groups:
            return

        min_prefix = {
            "A": 100,
            "B": 1000,
            "C": 6000,
            "D": 7000,
        }[group_key]
        max_prefix = section_group_end_prefixes[group_key]

        rows_for_group = [
            row
            for prefix, row in section_total_rows_by_prefix.items()
            if prefix.isdigit() and min_prefix <= int(prefix) <= max_prefix
        ]
        rows_for_group.sort()

        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=10)
        label_cell = ws.cell(row=row_idx, column=1, value=group_labels[group_key])
        label_cell.font = _BOLD
        label_cell.alignment = _LEFT
        label_cell.fill = _LIGHT_GRAY_FILL

        if rows_for_group:
            amount_formula = f"=SUM({','.join(f'K{r}' for r in rows_for_group)})"
        else:
            amount_formula = "=0"

        amount_cell = ws.cell(row=row_idx, column=11, value=amount_formula)
        amount_cell.font = _BOLD
        amount_cell.alignment = _RIGHT
        amount_cell.fill = _LIGHT_GRAY_FILL
        amount_cell.number_format = CURRENCY_FORMAT

        _set_outline_border(row_idx, row_idx)
        row_idx += 2
        emitted_groups.add(group_key)

    for prefix in sorted(grouped.keys(), key=_prefix_sort_key):
        if prefix.isdigit():
            prefix_num = int(prefix)
            for group_key in ("A", "B", "C", "D"):
                if group_key in emitted_groups:
                    continue
                if prefix_num > section_group_end_prefixes[group_key]:
                    _emit_group_total(group_key)

        section_start = row_idx

        label = topsheet_name_by_prefix.get(prefix, "")
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=11)
        section_cell = ws.cell(
            row=row_idx,
            column=1,
            value=f"{_format_topsheet_code(prefix)}  {label}".strip(),
        )
        section_cell.font = _BOLD
        section_cell.alignment = _LEFT
        section_cell.fill = _LIGHT_GRAY_FILL
        row_idx += 1

        section_detail_start = row_idx
        for detail in sorted(grouped[prefix], key=lambda r: (_normalize_account_code(r.account), r.description)):
            normalized = _normalize_account_code(detail.account)
            account_desc = category_by_account.get(normalized, "")

            row_data = [
                detail.account,
                account_desc,
                detail.description,
                detail.amount,
                detail.unit,
                "x",
                detail.unit2,
                detail.currency,
                detail.rate,
                detail.unit3,
                detail.subtotal,
            ]

            for col, value in enumerate(row_data, start=1):
                cell = ws.cell(row=row_idx, column=col, value=value)
                cell.font = _NORMAL
                cell.border = _NO_BORDER
                if col in (1, 2, 3):
                    cell.alignment = _LEFT
                elif col in (4, 11):
                    cell.alignment = _RIGHT
                else:
                    cell.alignment = _CENTER
                if col in (4, 9, 11) and isinstance(value, (int, float)):
                    cell.number_format = CURRENCY_FORMAT

            row_idx += 1

        section_detail_end = row_idx - 1

        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=10)
        total_label = ws.cell(row=row_idx, column=1, value=f"{_format_topsheet_code(prefix)} TOTAL")
        total_label.font = _BOLD
        total_label.alignment = _LEFT
        total_label.fill = _LIGHT_GRAY_FILL

        total_formula = f"=SUM(K{section_detail_start}:K{section_detail_end})"
        total_value = ws.cell(row=row_idx, column=11, value=total_formula)
        total_value.font = _BOLD
        total_value.alignment = _RIGHT
        total_value.fill = _LIGHT_GRAY_FILL
        total_value.number_format = CURRENCY_FORMAT
        section_total_rows_by_prefix[prefix] = row_idx

        _set_outline_border(section_start, row_idx)
        row_idx += 2

    for group_key in ("A", "B", "C", "D"):
        _emit_group_total(group_key)

    # ── Grand Total row ──────────────────────────────────────────────────────
    all_section_rows = sorted(section_total_rows_by_prefix.values())
    ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=10)
    gt_label = ws.cell(row=row_idx, column=1, value="GRAND TOTAL")
    gt_label.font = _WHITE_BOLD
    gt_label.alignment = _LEFT
    gt_label.fill = _GRAND_TOTAL_FILL

    if all_section_rows:
        refs = ",".join(f"K{r}" for r in all_section_rows)
        gt_val = ws.cell(row=row_idx, column=11, value=f"=SUM({refs})")
    else:
        gt_val = ws.cell(row=row_idx, column=11, value=0)
    gt_val.font = _WHITE_BOLD
    gt_val.alignment = _RIGHT
    gt_val.fill = _GRAND_TOTAL_FILL
    gt_val.number_format = CURRENCY_FORMAT

    for col in range(1, 12):
        ws.cell(row=row_idx, column=col).border = _THIN_BORDER

    ws.freeze_panes = "A2"


# ---------------------------------------------------------------------------
# Breakout Budget worksheet builder
# ---------------------------------------------------------------------------

_PERCENTAGE_FORMAT = '0.00%'

# ---------------------------------------------------------------------------
# Breakout Budget bible
# ---------------------------------------------------------------------------
# Maps 4-digit account code to a 6-tuple:
#   (non_prov_out, prov_labour, fed_labour, prov_svc_labour, svc_property, fed_svc_labour)
#
#   non_prov_out  – True  → entire Grand Total is Non-Provincial Spend
#   others        – float → that fraction of Grand Total qualifies for the column
#                   0.0  → not eligible (blank or explicit "-" in source bible)
BREAKOUT_BIBLE: dict[str, tuple] = {
    "0201": (False, 0.65, 0.65, 0.10, 0.0, 0.10),
    "0220": (False, 1.00, 1.00, 0.10, 0.0, 0.10),
    "0225": (False, 1.00, 1.00, 0.0,  0.0, 1.00),
    "0227": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "0295": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "0301": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "0395": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "0401": (False, 0.58, 1.00, 0.58, 0.0, 1.00),
    "0405": (False, 0.58, 1.00, 0.58, 0.0, 1.00),
    "0407": (False, 0.65, 0.65, 0.65, 0.0, 0.65),
    "0408": (False, 0.65, 0.65, 0.65, 0.0, 0.65),
    "0410": (False, 0.65, 0.65, 0.65, 0.0, 0.65),
    "0415": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "0417": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "0460": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "0465": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "0501": (False, 0.65, 0.65, 0.65, 0.0, 0.65),
    "0560": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "0565": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "0660": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "0665": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "1001": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1010": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1025": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1070": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "1075": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "1090": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "1092": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "1095": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "1110": (False, 1.00, 1.00, 0.0,  0.0, 1.00),
    "1170": (False, 1.00, 1.00, 0.0,  0.0, 1.00),
    "1201": (False, 0.80, 0.85, 0.80, 0.0, 0.85),
    "1205": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1210": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1215": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1220": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1223": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1228": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1235": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1240": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1243": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1245": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1248": (False, 0.85, 0.85, 0.85, 0.0, 0.85),
    "1250": (False, 0.85, 0.90, 0.85, 0.0, 0.90),
    "1252": (False, 0.85, 0.90, 0.85, 0.0, 0.90),
    "1261": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1262": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1270": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1301": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1310": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1312": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1320": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1335": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1350": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1420": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1425": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1501": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1505": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1510": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1515": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1530": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1601": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1610": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1693": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "1701": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1710": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1905": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1910": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "1993": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "2001": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2010": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2060": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2070": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2093": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "2101": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2110": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2112": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2170": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2201": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2205": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2210": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2211": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2212": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2250": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2260": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "2265": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "2270": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2301": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2310": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2320": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2350": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2401": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2410": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2501": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2801": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "2810": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "2815": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "2820": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "2830": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "2835": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "2840": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "2901": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "2905": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "2955": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "3105": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3106": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3110": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3150": (False, 1.00, 1.00, 1.00, 1.00, 1.00),
    "3152": (False, 1.00, 1.00, 1.00, 1.00, 1.00),
    "3160": (False, 1.00, 1.00, 1.00, 1.00, 1.00),
    "3195": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3201": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3210": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3215": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3218": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3225": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3245": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3301": (True,  0.0,  0.0,  0.0,  0.0,  0.0),
    "3310": (True,  0.0,  0.0,  0.0,  0.0,  0.0),
    "3320": (True,  0.0,  0.0,  0.0,  0.0,  0.0),
    "3330": (False, 0.0,  0.0,  0.0,  0.0,  0.0),
    "3335": (False, 0.0,  0.0,  0.0,  0.0,  0.0),
    "3350": (True,  0.0,  0.0,  0.0,  0.0,  0.0),
    "3395": (True,  0.0,  0.0,  0.0,  0.0,  0.0),
    "3401": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3405": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3430": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3440": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3445": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3447": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3510": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3515": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3545": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3710": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3730": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3740": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3810": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3830": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3850": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3910": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "3930": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4110": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4130": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4140": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4148": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4210": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4212": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4222": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4240": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4510": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4512": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4515": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4525": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4530": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4595": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4610": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4612": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4630": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4710": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4712": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4795": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4810": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4812": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4816": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4828": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "4830": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "5001": (False, 0.0,  0.0,  0.0,  1.00, 0.0),
    "6001": (False, 0.75, 0.75, 0.75, 0.0,  0.75),
    "6002": (False, 1.00, 1.00, 1.00, 0.0,  1.00),
    "6003": (False, 0.75, 0.75, 0.75, 0.0,  0.75),
    "6010": (False, 1.00, 1.00, 1.00, 0.0,  1.00),
    "6012": (False, 1.00, 1.00, 1.00, 0.0,  1.00),
    "6020": (False, 1.00, 1.00, 1.00, 0.0,  1.00),
    "6042": (False, 1.00, 1.00, 1.00, 0.0,  1.00),
    "6070": (False, 1.00, 1.00, 1.00, 0.0,  1.00),
    "6101": (False, 0.0,  0.0,  0.0,  0.0,  0.0),
    "6110": (False, 0.0,  0.0,  0.0,  0.0,  0.0),
    "6215": (False, 1.00, 1.00, 1.00, 0.0,  1.00),
    "6221": (False, 0.13, 0.13, 0.13, 0.0,  0.13),
    "6240": (False, 0.13, 0.13, 0.13, 0.0,  0.13),
    "6260": (False, 0.13, 0.13, 0.13, 0.0,  0.13),
    "6264": (False, 0.13, 0.13, 0.13, 0.0,  0.13),
    "6310": (False, 0.13, 0.13, 0.0,  1.00, 0.13),
    "6325": (False, 0.13, 0.13, 0.0,  1.00, 0.13),
    "6610": (False, 1.00, 1.00, 1.00, 0.0, 1.00),
    "6670": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "6695": (True,  1.00, 0.0,  0.0,  0.0, 1.00),
    "6701": (False, 0.13, 0.13, 0.0,  0.0, 0.13),
    "6710": (False, 0.13, 0.13, 0.0,  0.0, 0.13),
    "6730": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "6795": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "6801": (False, 0.13, 0.13, 0.13, 0.0, 0.13),
    "6890": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "6892": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "7001": (True,  1.00, 0.0,  0.0,  0.0, 1.00),
    "7025": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "7040": (True,  1.00, 0.0,  0.0,  0.0, 1.00),
    "7095": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "7101": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "7110": (True,  0.65, 0.0,  0.0,  0.0, 0.65),
    "7120": (True,  1.00, 0.0,  0.0,  0.0, 1.00),
    "7125": (True,  1.00, 0.0,  0.0,  0.0, 1.00),
    "7130": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "7201": (False, 0.37, 0.70, 0.0,  0.0, 0.70),
    "7210": (True,  1.00, 0.0,  0.0,  0.0, 1.00),
    "7220": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "7230": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
    "7295": (True,  0.0,  0.0,  0.0,  0.0, 0.0),
    "8001": (False, 0.0,  0.0,  0.0,  0.0, 0.0),
}

# Maps account prefix numeric range to a group label for the Groups column
def _derive_group_label(prefix: str) -> str:
    """Return the A/B/C/D group label for a given 4-digit prefix (e.g. '0200')."""
    if not prefix.isdigit():
        return ""
    n = int(prefix)
    if 100 <= n <= 600:
        return 'A \u2013 Above the Line'
    elif 1000 <= n <= 5900:
        return 'B \u2013 Production'
    elif 6000 <= n <= 6900:
        return 'C \u2013 Post-Production'
    elif 7000 <= n <= 7200:
        return 'D \u2013 Other'
    return ""


def _write_breakout_budget(ws, budget: ParsedBudget, overrides: dict | None = None) -> None:
    """Generate the Breakout Budget tab.

    Fixed columns (A–I):
      A: Account
      B: Account Description (from line_items / categories)
      C: Description
      D: Agg%
      E: Groups  (from source Excel, or derived A/B/C/D label)
      F: Currency
      G: Subtotal
      H: Fringes  (= G × D for rows with an Agg%)
      I: Grand Total (= G + H)

    Fixed analysis columns (J–AA, columns 10–27; currencies at end):
      J  (10): Foreign              – "FOR" when currency is not CAD/CA
      K  (11): Foreign Spend        – Grand Total if Foreign = "FOR"
      L  (12): Canadian Spend       – Grand Total minus Foreign Spend
      M  (13): Fed Labour %         – basis %
      N  (14): Federal Labour       – calc $
      O  (15): Fed Svc Labour %     – basis %
      P  (16): Federal Svc Labour   – calc $
      Q  (17): Non-Prov             – "OUT" when account is non-provincial
      R  (18): Non-Provincial Spend – calc $
      S  (19): Provincial Spend     – Grand Total minus Non-Provincial Spend
      T  (20): Prov Labour %        – basis %
      U  (21): Provincial Labour    – calc $
      V  (22): Prov Svc Labour %    – basis %
      W  (23): Svc Property %       – basis %
      X  (24): Provincial Svc Labour– calc $
      Y  (25): Services Property    – calc $
      Z  (26): Internals            – Grand Total for Internal OH rows
      AA (27): Meals                – Grand Total for meal/per-diem rows

    Dynamic currency columns (28+):
      One "XXX Grand Total" column per distinct currency found in the data.
    """
    ws.title = "Breakout Budget"

    # ── Build category lookup ────────────────────────────────────────────────
    category_by_account: dict[str, str] = {}
    for item in budget.line_items:
        category_by_account[_normalize_account_code(item.code)] = item.description

    # ── Filter & group detail rows ───────────────────────────────────────────
    # Exclude zero-subtotal rows and "Total Fringes" rows (fringes are calculated in col H)
    detail_rows = [
        r for r in budget.detail_rows
        if r.subtotal > 0 and "total fringes" not in r.description.lower()
    ]

    # ── Discover distinct currencies (sorted) ────────────────────────────────
    seen_currencies: list[str] = []
    for r in detail_rows:
        cur = (r.currency or "").strip().upper()
        if cur and cur not in seen_currencies:
            seen_currencies.append(cur)
    seen_currencies.sort()

    # Fixed analysis columns (A–I = 1–9; analysis columns 10–27; currencies at end)
    #
    # 10: Foreign              – "FOR" indicator
    # 11: Foreign Spend        – Grand Total when Foreign = "FOR"
    # 12: Canadian Spend       – Grand Total minus Foreign Spend
    # 13: Fed Labour %         – basis %
    # 14: Federal Labour       – calc $
    # 15: Fed Svc Labour %     – basis %
    # 16: Federal Svc Labour   – calc $
    # 17: Non-Prov             – "OUT" indicator
    # 18: Non-Provincial Spend – calc $
    # 19: Provincial Spend     – Grand Total minus Non-Provincial Spend
    # 20: Prov Labour %        – basis %
    # 21: Provincial Labour    – calc $
    # 22: Prov Svc Labour %    – basis %
    # 23: Svc Property %       – basis %
    # 24: Provincial Svc Labour– calc $
    # 25: Services Property    – calc $
    # 26: Internals            – Grand Total for Internal OH rows
    # 27: Meals                – Grand Total for meal/per-diem rows
    # 28+: one column per distinct currency
    foreign_col: int                  = 10
    foreign_spend_calc_col: int       = 11
    canadian_spend_calc_col: int      = 12
    fed_labour_basis_col: int         = 13
    fed_labour_calc_col: int          = 14
    fed_svc_basis_col: int            = 15
    fed_svc_calc_col: int             = 16
    non_prov_basis_col: int           = 17
    non_prov_calc_col: int            = 18
    provincial_spend_calc_col: int    = 19
    prov_labour_basis_col: int        = 20
    prov_labour_calc_col: int         = 21
    prov_svc_basis_col: int           = 22
    svc_property_basis_col: int       = 23
    prov_svc_calc_col: int            = 24
    svc_property_calc_col: int        = 25
    internals_col: int                = 26
    meals_col: int                    = 27

    # Currency grand-total columns come after all fixed columns
    currency_col_map: dict[str, int] = {
        cur: 27 + i + 1 for i, cur in enumerate(seen_currencies)
    }

    # basis_cols order must match raw_basis tuple from BREAKOUT_BIBLE:
    #   [non_prov_out, prov_labour, fed_labour, prov_svc, svc_property, fed_svc]
    basis_cols: list[int] = [
        non_prov_basis_col, prov_labour_basis_col, fed_labour_basis_col,
        prov_svc_basis_col, svc_property_basis_col, fed_svc_basis_col,
    ]
    # calc_cols order must match calc_formulas list in the per-row section below
    calc_cols: list[int] = [
        non_prov_calc_col, prov_labour_calc_col, fed_labour_calc_col,
        prov_svc_calc_col, svc_property_calc_col, fed_svc_calc_col,
        foreign_spend_calc_col,
    ]
    # Pre-compute column letters once (used in per-row formula strings)
    basis_letters = [get_column_letter(c) for c in basis_cols]

    # ── Headers & widths ─────────────────────────────────────────────────────
    headers = [
        "Account",
        "Account Description",
        "Description",
        "Agg%",
        "Groups",
        "Currency",
        "Subtotal",
        "Fringes",
        "Grand Total",
        # cols 10–12: Foreign indicator, Foreign Spend, Canadian Spend
        "Foreign",
        "Foreign Spend",
        "Canadian Spend",
        # cols 13–16: Federal
        "Fed Labour %",
        "Federal Labour",
        "Fed Svc Labour %",
        "Federal Services Labour",
        # cols 17–19: Non-Provincial
        "Non-Prov",
        "Non-Provincial Spend",
        "Provincial Spend",
        # cols 20–25: Provincial
        "Prov Labour %",
        "Provincial Labour",
        "Prov Svc Labour %",
        "Svc Property %",
        "Provincial Services Labour",
        "Services Property",
        # cols 26–27: Internals, Meals
        "Internals",
        "Meals",
    ] + [f"{cur} Grand Total" for cur in seen_currencies]

    num_cols = len(headers)
    widths = (
        [12, 34, 40, 8, 28, 10, 14, 14, 14]    # A–I
        + [10, 18, 18]                           # Foreign, Foreign Spend, Canadian Spend
        + [13, 18, 16, 24]                       # Fed Labour %, Federal Labour, Fed Svc Labour %, Federal Services Labour
        + [10, 22, 22]                           # Non-Prov, Non-Provincial Spend, Provincial Spend
        + [13, 20, 16, 13, 26, 20]              # Prov Labour %, Provincial Labour, Prov Svc Labour %, Svc Property %, Provincial Services Labour, Services Property
        + [16, 14]                               # Internals, Meals
        + [16] * len(seen_currencies)            # currency grand total cols
    )

    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width

    # ── Column groups (collapsed by default, expandable) ─────────────────────
    _HIDDEN_GROUPS = [
        [4, 5],           # D–E:   Agg%, Groups
        [15, 16],         # O–P:   Fed Svc Labour %, Federal Services Labour
        [22, 23, 24, 25], # V–Y:   Prov Svc Labour %, Svc Property %, Provincial Services Labour, Services Property
    ]
    for group in _HIDDEN_GROUPS:
        for col in group:
            cd = ws.column_dimensions[get_column_letter(col)]
            cd.outlineLevel = 1
            cd.hidden = True

    # ── Header row ──────────────────────────────────────────────────────────
    for col, label in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=label)
        cell.font = _BOLD
        cell.alignment = _LEFT if col in (1, 2, 3, 5) else _CENTER
        cell.border = _NO_BORDER
        cell.fill = _LIGHT_GRAY_FILL

    # Outer border on header row
    for col in range(1, num_cols + 1):
        c = ws.cell(row=1, column=col)
        c.border = Border(left=c.border.left, right=c.border.right, top=_THIN, bottom=_THIN)
    ws.cell(row=1, column=1).border = Border(
        left=_THIN,
        right=ws.cell(row=1, column=1).border.right,
        top=ws.cell(row=1, column=1).border.top,
        bottom=ws.cell(row=1, column=1).border.bottom,
    )
    ws.cell(row=1, column=num_cols).border = Border(
        left=ws.cell(row=1, column=num_cols).border.left,
        right=_THIN,
        top=ws.cell(row=1, column=num_cols).border.top,
        bottom=ws.cell(row=1, column=num_cols).border.bottom,
    )

    topsheet_name_by_prefix = {
        _cavco_to_mm_prefix(entry[0]): entry[1]
        for entry in TOPSHEET_STRUCTURE
        if len(entry) == 2 and entry[0] not in ("HEADER", "BLANK", "GRAND_TOTAL")
    }

    grouped: dict[str, list] = {}
    for row in detail_rows:
        prefix = _topsheet_prefix_from_account(row.account)
        if not prefix:
            continue
        grouped.setdefault(prefix, []).append(row)

    # ── Outline border helper ────────────────────────────────────────────────
    def _set_outline_border_bb(start_row: int, end_row: int) -> None:
        for col in range(1, num_cols + 1):
            top_cell = ws.cell(row=start_row, column=col)
            top_cell.border = Border(
                left=top_cell.border.left, right=top_cell.border.right,
                top=_THIN, bottom=top_cell.border.bottom,
            )
            bottom_cell = ws.cell(row=end_row, column=col)
            bottom_cell.border = Border(
                left=bottom_cell.border.left, right=bottom_cell.border.right,
                top=bottom_cell.border.top, bottom=_THIN,
            )
        for row in range(start_row, end_row + 1):
            left_cell = ws.cell(row=row, column=1)
            left_cell.border = Border(
                left=_THIN, right=left_cell.border.right,
                top=left_cell.border.top, bottom=left_cell.border.bottom,
            )
            right_cell = ws.cell(row=row, column=num_cols)
            right_cell.border = Border(
                left=right_cell.border.left, right=_THIN,
                top=right_cell.border.top, bottom=right_cell.border.bottom,
            )

    # ── Group totals logic ───────────────────────────────────────────────────
    row_idx = 4  # rows 2–3 reserved for pinned summary (written after grand total is known)
    section_total_rows_by_prefix: dict[str, int] = {}

    section_group_end_prefixes = {"A": 600, "B": 5900, "C": 6900, "D": 7200}
    group_labels = {
        "A": 'TOTAL "A" \u2013 ABOVE THE LINE',
        "B": 'TOTAL PRODUCTION "B"',
        "C": 'TOTAL POST-PRODUCTION "C"',
        "D": 'TOTAL OTHER "D"',
    }
    emitted_groups: set[str] = set()

    def _emit_group_total_bb(group_key: str) -> None:
        nonlocal row_idx
        if group_key in emitted_groups:
            return

        min_prefix = {"A": 100, "B": 1000, "C": 6000, "D": 7000}[group_key]
        max_prefix = section_group_end_prefixes[group_key]

        rows_for_group = sorted(
            row
            for prefix, row in section_total_rows_by_prefix.items()
            if prefix.isdigit() and min_prefix <= int(prefix) <= max_prefix
        )

        # Merge A-F for the label
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=6)
        label_cell = ws.cell(row=row_idx, column=1, value=group_labels[group_key])
        label_cell.font = _BOLD
        label_cell.alignment = _LEFT
        label_cell.fill = _LIGHT_GRAY_FILL

        if rows_for_group:
            refs_g = ','.join(f'G{r}' for r in rows_for_group)
            refs_h = ','.join(f'H{r}' for r in rows_for_group)
            refs_i = ','.join(f'I{r}' for r in rows_for_group)
            subtotal_formula   = f"=SUM({refs_g})"
            fringes_formula    = f"=SUM({refs_h})"
            grandtotal_formula = f"=SUM({refs_i})"
        else:
            subtotal_formula = fringes_formula = grandtotal_formula = "=0"

        for col, formula in zip((7, 8, 9), (subtotal_formula, fringes_formula, grandtotal_formula)):
            c = ws.cell(row=row_idx, column=col, value=formula)
            c.font = _BOLD
            c.alignment = _RIGHT
            c.fill = _LIGHT_GRAY_FILL
            c.number_format = _ACCOUNTING_FORMAT

        # Currency grand total columns
        for cur, col in currency_col_map.items():
            letter = get_column_letter(col)
            if rows_for_group:
                refs = ','.join(f'{letter}{r}' for r in rows_for_group)
                formula = f"=SUM({refs})"
            else:
                formula = "=0"
            c = ws.cell(row=row_idx, column=col, value=formula)
            c.font = _BOLD
            c.alignment = _RIGHT
            c.fill = _LIGHT_GRAY_FILL
            c.number_format = _ACCOUNTING_FORMAT

        # Internals column for group total
        internals_letter = get_column_letter(internals_col)
        if rows_for_group:
            refs = ','.join(f'{internals_letter}{r}' for r in rows_for_group)
            internals_formula = f"=SUM({refs})"
        else:
            internals_formula = "=0"
        c = ws.cell(row=row_idx, column=internals_col, value=internals_formula)
        c.font = _BOLD
        c.alignment = _RIGHT
        c.fill = _LIGHT_GRAY_FILL
        c.number_format = _ACCOUNTING_FORMAT

        # Meals column for group total
        meals_letter = get_column_letter(meals_col)
        if rows_for_group:
            refs = ','.join(f'{meals_letter}{r}' for r in rows_for_group)
            meals_formula = f"=SUM({refs})"
        else:
            meals_formula = "=0"
        c = ws.cell(row=row_idx, column=meals_col, value=meals_formula)
        c.font = _BOLD
        c.alignment = _RIGHT
        c.fill = _LIGHT_GRAY_FILL
        c.number_format = _ACCOUNTING_FORMAT

        # Bible basis cols + Foreign: blank at aggregate rows (% not meaningful)
        for bcol in [foreign_col] + basis_cols:
            c = ws.cell(row=row_idx, column=bcol, value=None)
            c.fill = _LIGHT_GRAY_FILL

        # Canadian Spend: Grand Total minus Foreign Spend at this aggregate row
        fs_letter = get_column_letter(foreign_spend_calc_col)
        c = ws.cell(row=row_idx, column=canadian_spend_calc_col,
                    value=f"=I{row_idx}-{fs_letter}{row_idx}")
        c.font = _BOLD
        c.alignment = _RIGHT
        c.fill = _LIGHT_GRAY_FILL
        c.number_format = _ACCOUNTING_FORMAT

        # Provincial Spend: Grand Total minus Non-Provincial Spend at this aggregate row
        np_calc_letter = get_column_letter(non_prov_calc_col)
        c = ws.cell(row=row_idx, column=provincial_spend_calc_col,
                    value=f"=I{row_idx}-{np_calc_letter}{row_idx}")
        c.font = _BOLD
        c.alignment = _RIGHT
        c.fill = _LIGHT_GRAY_FILL
        c.number_format = _ACCOUNTING_FORMAT

        # Bible calc cols: SUM of section total rows
        for ccol in calc_cols:
            cletter = get_column_letter(ccol)
            if rows_for_group:
                refs = ','.join(f'{cletter}{r}' for r in rows_for_group)
                cformula = f"=SUM({refs})"
            else:
                cformula = "=0"
            c = ws.cell(row=row_idx, column=ccol, value=cformula)
            c.font = _BOLD
            c.alignment = _RIGHT
            c.fill = _LIGHT_GRAY_FILL
            c.number_format = _ACCOUNTING_FORMAT

        _set_outline_border_bb(row_idx, row_idx)
        row_idx += 2
        emitted_groups.add(group_key)

    # ── Main iteration over prefix groups ───────────────────────────────────
    for prefix in sorted(grouped.keys(), key=_prefix_sort_key):
        if prefix.isdigit():
            prefix_num = int(prefix)
            for group_key in ("A", "B", "C", "D"):
                if group_key in emitted_groups:
                    continue
                if prefix_num > section_group_end_prefixes[group_key]:
                    _emit_group_total_bb(group_key)

        section_start = row_idx
        label = topsheet_name_by_prefix.get(prefix, "")

        # Section header (no merge — fill applied to every cell in the row)
        section_cell = ws.cell(
            row=row_idx,
            column=1,
            value=f"{_format_topsheet_code(prefix)}  {label}".strip(),
        )
        section_cell.font = _BOLD
        section_cell.alignment = _LEFT
        section_cell.fill = _LIGHT_GRAY_FILL
        for col in range(2, num_cols + 1):
            ws.cell(row=row_idx, column=col).fill = _LIGHT_GRAY_FILL
        row_idx += 1

        section_detail_start = row_idx

        for detail in sorted(grouped[prefix], key=lambda r: (_normalize_account_code(r.account), r.description)):
            normalized = _normalize_account_code(detail.account)
            account_desc = category_by_account.get(normalized, "")
            group_label = detail.groups if detail.groups else _derive_group_label(prefix)
            is_fringes_row = detail.agg is not None and detail.agg > 0

            subtotal_col = f"G{row_idx}"
            agg_col = f"D{row_idx}"

            row_data = [
                (detail.account,     _LEFT,   None),
                (account_desc,       _LEFT,   None),
                (detail.description, _LEFT,   None),
                (detail.agg,         _CENTER, _PERCENTAGE_FORMAT),
                (group_label,        _LEFT,   None),
                (detail.currency,    _CENTER, None),
                (detail.subtotal,    _RIGHT,  _ACCOUNTING_FORMAT),
                (f"={subtotal_col}*{agg_col}" if is_fringes_row else 0, _RIGHT, _ACCOUNTING_FORMAT),
                (f"=G{row_idx}+H{row_idx}", _RIGHT, _ACCOUNTING_FORMAT),
            ]

            for col, (value, align, num_fmt) in enumerate(row_data, start=1):
                cell = ws.cell(row=row_idx, column=col, value=value)
                cell.font = _NORMAL
                cell.border = _NO_BORDER
                cell.alignment = align
                if num_fmt:
                    cell.number_format = num_fmt

            # Currency grand total columns: =I{row} if matching currency, else 0
            row_currency = (detail.currency or "").strip().upper()
            for cur, col in currency_col_map.items():
                value = f"=I{row_idx}" if row_currency == cur else 0
                c = ws.cell(row=row_idx, column=col, value=value)
                c.font = _NORMAL
                c.border = _NO_BORDER
                c.alignment = _RIGHT
                c.number_format = _ACCOUNTING_FORMAT

            # Internals column: if "Internal OH" appears anywhere in the Groups cell (E), return grand total
            internals_value = f'=IF(ISNUMBER(SEARCH("Internal OH",E{row_idx})),I{row_idx},0)'
            c = ws.cell(row=row_idx, column=internals_col, value=internals_value)
            c.font = _NORMAL
            c.border = _NO_BORDER
            c.alignment = _RIGHT
            c.number_format = _ACCOUNTING_FORMAT

            # Meals column: account in {2840,3201,3210,3215,3320} OR "Diem" in Description (col C)
            meals_value = (
                f'=IF(OR(ISNUMBER(SEARCH("Diem",C{row_idx})),'
                f'A{row_idx}="2840",A{row_idx}="3201",A{row_idx}="3210",A{row_idx}="3215",A{row_idx}="3320"),'
                f'I{row_idx},0)'
            )
            c = ws.cell(row=row_idx, column=meals_col, value=meals_value)
            c.font = _NORMAL
            c.border = _NO_BORDER
            c.alignment = _RIGHT
            c.number_format = _ACCOUNTING_FORMAT

            # ── Bible basis columns: visible raw treatment from BREAKOUT_BIBLE ──
            # Overrides (if any) supersede the bible; None fields fall back to bible.
            ov = (overrides or {}).get(normalized)
            bible_entry = BREAKOUT_BIBLE.get(normalized)
            if bible_entry:
                b_non_prov_out, b_pl, b_fl, b_psl, b_sp, b_fsl = bible_entry
            else:
                b_non_prov_out, b_pl, b_fl, b_psl, b_sp, b_fsl = False, 0.0, 0.0, 0.0, 0.0, 0.0

            def _ov_val(override_val, bible_val):
                """Return override if set, else bible value."""
                return bible_val if override_val is None else override_val

            if ov is not None:
                # Support both Pydantic model and plain dict
                _get = (lambda f: getattr(ov, f)) if hasattr(ov, "__fields__") else (lambda f: ov.get(f))
                non_prov_out = _ov_val(_get("is_non_prov"), b_non_prov_out)
                pl  = _ov_val(_get("prov_labour_pct"),     b_pl)
                fl  = _ov_val(_get("fed_labour_pct"),      b_fl)
                psl = _ov_val(_get("prov_svc_labour_pct"), b_psl)
                sp  = _ov_val(_get("svc_property_pct"),    b_sp)
                fsl = _ov_val(_get("fed_svc_labour_pct"),  b_fsl)
                is_foreign_override = _get("is_foreign")  # None / True / False
            else:
                non_prov_out, pl, fl, psl, sp, fsl = b_non_prov_out, b_pl, b_fl, b_psl, b_sp, b_fsl
                is_foreign_override = None

            raw_basis = [
                "OUT" if non_prov_out else None,
                pl   if pl  > 0 else None,
                fl   if fl  > 0 else None,
                psl  if psl > 0 else None,
                sp   if sp  > 0 else None,
                fsl  if fsl > 0 else None,
            ]

            for bcol, bval in zip(basis_cols, raw_basis):
                c = ws.cell(row=row_idx, column=bcol, value=bval)
                c.font = _NORMAL
                c.border = _NO_BORDER
                c.alignment = _CENTER
                if isinstance(bval, float):
                    c.number_format = _PERCENTAGE_FORMAT

            # Foreign column: Excel formula by default; hard-coded when overridden
            if is_foreign_override is True:
                foreign_value = "FOR"
            elif is_foreign_override is False:
                foreign_value = ""
            else:
                foreign_value = (
                    f'=IF(AND(F{row_idx}<>"",F{row_idx}<>"CAD",F{row_idx}<>"CA"),"FOR","")'
                )
            c = ws.cell(row=row_idx, column=foreign_col, value=foreign_value)
            c.font = _NORMAL
            c.border = _NO_BORDER
            c.alignment = _CENTER

            # Canadian Spend: Grand Total minus Foreign Spend (auditable formula)
            fs_letter = get_column_letter(foreign_spend_calc_col)
            canadian_formula = f"=I{row_idx}-{fs_letter}{row_idx}"
            c = ws.cell(row=row_idx, column=canadian_spend_calc_col, value=canadian_formula)
            c.font = _NORMAL
            c.border = _NO_BORDER
            c.alignment = _RIGHT
            c.number_format = _ACCOUNTING_FORMAT

            # ── Bible calc columns: IF formulas referencing the basis columns ──
            np_l, pl_l, fl_l, psl_l, sp_l, fsl_l = basis_letters
            for_l = get_column_letter(foreign_col)
            calc_formulas = [
                # Non-Provincial Spend: triggered by either "OUT" (bible) or "FOR" (foreign currency)
                f'=IF(OR({np_l}{row_idx}="OUT",{for_l}{row_idx}="FOR"),I{row_idx},0)',
                f'=IF({pl_l}{row_idx}>0,G{row_idx}*{pl_l}{row_idx},0)',
                f'=IF({fl_l}{row_idx}>0,G{row_idx}*{fl_l}{row_idx},0)',
                f'=IF({psl_l}{row_idx}>0,G{row_idx}*{psl_l}{row_idx},0)',
                f'=IF({sp_l}{row_idx}>0,I{row_idx}*{sp_l}{row_idx},0)',
                f'=IF({fsl_l}{row_idx}>0,G{row_idx}*{fsl_l}{row_idx},0)',
                # Foreign Spend: Grand Total when the Foreign column reads "FOR"
                f'=IF({for_l}{row_idx}="FOR",I{row_idx},0)',
            ]
            for ccol, cval in zip(calc_cols, calc_formulas):
                c = ws.cell(row=row_idx, column=ccol, value=cval)
                c.font = _NORMAL
                c.border = _NO_BORDER
                c.alignment = _RIGHT
                c.number_format = _ACCOUNTING_FORMAT

            # Provincial Spend: Grand Total minus Non-Provincial Spend (auditable formula)
            np_calc_letter = get_column_letter(non_prov_calc_col)
            c = ws.cell(row=row_idx, column=provincial_spend_calc_col,
                        value=f"=I{row_idx}-{np_calc_letter}{row_idx}")
            c.font = _NORMAL
            c.border = _NO_BORDER
            c.alignment = _RIGHT
            c.number_format = _ACCOUNTING_FORMAT

            row_idx += 1

        section_detail_end = row_idx - 1

        # Prefix total row
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=6)
        total_label_cell = ws.cell(row=row_idx, column=1, value=f"{_format_topsheet_code(prefix)} TOTAL")
        total_label_cell.font = _BOLD
        total_label_cell.alignment = _LEFT
        total_label_cell.fill = _LIGHT_GRAY_FILL

        for col, letter in zip((7, 8, 9), ("G", "H", "I")):
            formula = f"=SUM({letter}{section_detail_start}:{letter}{section_detail_end})"
            c = ws.cell(row=row_idx, column=col, value=formula)
            c.font = _BOLD
            c.alignment = _RIGHT
            c.fill = _LIGHT_GRAY_FILL
            c.number_format = _ACCOUNTING_FORMAT

        # Currency grand total columns for this section total
        for cur, col in currency_col_map.items():
            letter = get_column_letter(col)
            formula = f"=SUM({letter}{section_detail_start}:{letter}{section_detail_end})"
            c = ws.cell(row=row_idx, column=col, value=formula)
            c.font = _BOLD
            c.alignment = _RIGHT
            c.fill = _LIGHT_GRAY_FILL
            c.number_format = _ACCOUNTING_FORMAT

        # Internals column for this section total
        internals_letter = get_column_letter(internals_col)
        formula = f"=SUM({internals_letter}{section_detail_start}:{internals_letter}{section_detail_end})"
        c = ws.cell(row=row_idx, column=internals_col, value=formula)
        c.font = _BOLD
        c.alignment = _RIGHT
        c.fill = _LIGHT_GRAY_FILL
        c.number_format = _ACCOUNTING_FORMAT

        # Meals column for this section total
        meals_letter = get_column_letter(meals_col)
        formula = f"=SUM({meals_letter}{section_detail_start}:{meals_letter}{section_detail_end})"
        c = ws.cell(row=row_idx, column=meals_col, value=formula)
        c.font = _BOLD
        c.alignment = _RIGHT
        c.fill = _LIGHT_GRAY_FILL
        c.number_format = _ACCOUNTING_FORMAT

        # Bible basis cols + Foreign: blank at aggregate rows
        for bcol in [foreign_col] + basis_cols:
            c = ws.cell(row=row_idx, column=bcol, value=None)
            c.fill = _LIGHT_GRAY_FILL

        # Canadian Spend: Grand Total minus Foreign Spend at this section row
        fs_letter = get_column_letter(foreign_spend_calc_col)
        c = ws.cell(row=row_idx, column=canadian_spend_calc_col,
                    value=f"=I{row_idx}-{fs_letter}{row_idx}")
        c.font = _BOLD
        c.alignment = _RIGHT
        c.fill = _LIGHT_GRAY_FILL
        c.number_format = _ACCOUNTING_FORMAT

        # Provincial Spend: Grand Total minus Non-Provincial Spend at this section row
        np_calc_letter = get_column_letter(non_prov_calc_col)
        c = ws.cell(row=row_idx, column=provincial_spend_calc_col,
                    value=f"=I{row_idx}-{np_calc_letter}{row_idx}")
        c.font = _BOLD
        c.alignment = _RIGHT
        c.fill = _LIGHT_GRAY_FILL
        c.number_format = _ACCOUNTING_FORMAT

        # Bible calc cols: SUM of detail rows in this section
        for ccol in calc_cols:
            cletter = get_column_letter(ccol)
            formula = f"=SUM({cletter}{section_detail_start}:{cletter}{section_detail_end})"
            c = ws.cell(row=row_idx, column=ccol, value=formula)
            c.font = _BOLD
            c.alignment = _RIGHT
            c.fill = _LIGHT_GRAY_FILL
            c.number_format = _ACCOUNTING_FORMAT

        section_total_rows_by_prefix[prefix] = row_idx
        _set_outline_border_bb(section_start, row_idx)
        row_idx += 2

    # Emit any remaining group totals
    for group_key in ("A", "B", "C", "D"):
        _emit_group_total_bb(group_key)

    # ── Grand Total row ──────────────────────────────────────────────────────
    all_section_rows = sorted(section_total_rows_by_prefix.values())
    ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=6)
    gt_label = ws.cell(row=row_idx, column=1, value="GRAND TOTAL")
    gt_label.font = _WHITE_BOLD
    gt_label.alignment = _LEFT
    gt_label.fill = _GRAND_TOTAL_FILL

    if all_section_rows:
        for col, letter in zip((7, 8, 9), ("G", "H", "I")):
            refs = ",".join(f"{letter}{r}" for r in all_section_rows)
            c = ws.cell(row=row_idx, column=col, value=f"=SUM({refs})")
            c.font = _WHITE_BOLD
            c.alignment = _RIGHT
            c.fill = _GRAND_TOTAL_FILL
            c.number_format = _ACCOUNTING_FORMAT
        for cur, col in currency_col_map.items():
            letter = get_column_letter(col)
            refs = ",".join(f"{letter}{r}" for r in all_section_rows)
            c = ws.cell(row=row_idx, column=col, value=f"=SUM({refs})")
            c.font = _WHITE_BOLD
            c.alignment = _RIGHT
            c.fill = _GRAND_TOTAL_FILL
            c.number_format = _ACCOUNTING_FORMAT
        # Internals column for grand total
        internals_letter = get_column_letter(internals_col)
        refs = ",".join(f"{internals_letter}{r}" for r in all_section_rows)
        c = ws.cell(row=row_idx, column=internals_col, value=f"=SUM({refs})")
        c.font = _WHITE_BOLD
        c.alignment = _RIGHT
        c.fill = _GRAND_TOTAL_FILL
        c.number_format = _ACCOUNTING_FORMAT
        # Meals column for grand total
        meals_letter = get_column_letter(meals_col)
        refs = ",".join(f"{meals_letter}{r}" for r in all_section_rows)
        c = ws.cell(row=row_idx, column=meals_col, value=f"=SUM({refs})")
        c.font = _WHITE_BOLD
        c.alignment = _RIGHT
        c.fill = _GRAND_TOTAL_FILL
        c.number_format = _ACCOUNTING_FORMAT
        # Bible basis cols + Foreign: blank on grand total row
        for bcol in [foreign_col] + basis_cols:
            c = ws.cell(row=row_idx, column=bcol, value=None)
            c.font = _WHITE_BOLD
            c.fill = _GRAND_TOTAL_FILL

        # Canadian Spend: Grand Total minus Foreign Spend at the grand total row
        fs_letter = get_column_letter(foreign_spend_calc_col)
        c = ws.cell(row=row_idx, column=canadian_spend_calc_col,
                    value=f"=I{row_idx}-{fs_letter}{row_idx}")
        c.font = _WHITE_BOLD
        c.alignment = _RIGHT
        c.fill = _GRAND_TOTAL_FILL
        c.number_format = _ACCOUNTING_FORMAT

        # Provincial Spend: Grand Total minus Non-Provincial Spend at the grand total row
        np_calc_letter = get_column_letter(non_prov_calc_col)
        c = ws.cell(row=row_idx, column=provincial_spend_calc_col,
                    value=f"=I{row_idx}-{np_calc_letter}{row_idx}")
        c.font = _WHITE_BOLD
        c.alignment = _RIGHT
        c.fill = _GRAND_TOTAL_FILL
        c.number_format = _ACCOUNTING_FORMAT

        # Bible calc cols: SUM of section total rows
        for ccol in calc_cols:
            cletter = get_column_letter(ccol)
            refs = ",".join(f"{cletter}{r}" for r in all_section_rows)
            c = ws.cell(row=row_idx, column=ccol, value=f"=SUM({refs})")
            c.font = _WHITE_BOLD
            c.alignment = _RIGHT
            c.fill = _GRAND_TOTAL_FILL
            c.number_format = _ACCOUNTING_FORMAT
    else:
        for col in range(7, num_cols + 1):
            c = ws.cell(row=row_idx, column=col, value=0)
            c.font = _WHITE_BOLD
            c.alignment = _RIGHT
            c.fill = _GRAND_TOTAL_FILL
            c.number_format = _ACCOUNTING_FORMAT

    for col in range(1, num_cols + 1):
        ws.cell(row=row_idx, column=col).border = _THIN_BORDER

    # ── Pinned summary rows (written now that grand total row is known) ───────
    grand_total_row = row_idx

    # All dollar-amount columns (accounting format) — used in both summary rows
    accounting_cols = [
        7, 8, 9,
        foreign_spend_calc_col, canadian_spend_calc_col,
        fed_labour_calc_col, fed_svc_calc_col,
        non_prov_calc_col, provincial_spend_calc_col,
        prov_labour_calc_col, prov_svc_calc_col, svc_property_calc_col,
        internals_col, meals_col,
    ] + list(currency_col_map.values())

    # Apply background fill to every cell in both summary rows first
    for col in range(1, num_cols + 1):
        ws.cell(row=2, column=col).fill = _LIGHT_GRAY_FILL
        ws.cell(row=3, column=col).fill = _LIGHT_GRAY_FILL

    # Row 2 — TOTAL: mirror of grand total row
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=6)
    lbl2 = ws.cell(row=2, column=1, value="TOTAL")
    lbl2.font = _BOLD
    lbl2.alignment = _LEFT
    lbl2.fill = _LIGHT_GRAY_FILL
    for col in accounting_cols:
        letter = get_column_letter(col)
        c = ws.cell(row=2, column=col, value=f"={letter}{grand_total_row}")
        c.font = _BOLD
        c.alignment = _RIGHT
        c.fill = _LIGHT_GRAY_FILL
        c.number_format = _ACCOUNTING_FORMAT
    _set_outline_border_bb(2, 2)

    # Row 3 — % OF GRAND TOTAL: each accounting col as % of Grand Total (col I)
    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=6)
    lbl3 = ws.cell(row=3, column=1, value="% OF GRAND TOTAL")
    lbl3.font = _BOLD
    lbl3.alignment = _LEFT
    lbl3.fill = _LIGHT_GRAY_FILL
    for col in accounting_cols:
        letter = get_column_letter(col)
        c = ws.cell(row=3, column=col,
                    value=f"=IFERROR({letter}{grand_total_row}/I{grand_total_row},0)")
        c.font = _BOLD
        c.alignment = _RIGHT
        c.fill = _LIGHT_GRAY_FILL
        c.number_format = _PERCENTAGE_FORMAT
    _set_outline_border_bb(3, 3)

    # ── Conditional formatting: highlight indicator cells ────────────────────
    # Subtle rose fill for "FOR" (Foreign) and "OUT" (Non-Prov) flags
    _FLAG_FILL = PatternFill(start_color="FFDAD6", end_color="FFDAD6", fill_type="solid")
    _for_col  = get_column_letter(foreign_col)
    _nprov_col = get_column_letter(non_prov_basis_col)
    max_row = grand_total_row
    ws.conditional_formatting.add(
        f"{_for_col}1:{_for_col}{max_row}",
        CellIsRule(operator="equal", formula=['"FOR"'], fill=_FLAG_FILL),
    )
    ws.conditional_formatting.add(
        f"{_nprov_col}1:{_nprov_col}{max_row}",
        CellIsRule(operator="equal", formula=['"OUT"'], fill=_FLAG_FILL),
    )

    # ── Column-group outside borders ─────────────────────────────────────────
    # A medium border box is drawn around each logical column group, running
    # from the header row all the way down to the grand total row.
    _MED = Side(style="medium")
    col_groups = [
        (foreign_col,        fed_labour_calc_col),   # Foreign … Federal Labour     (10–14)
        (non_prov_basis_col, prov_labour_calc_col),  # Non-Prov … Provincial Labour (17–21)
        (internals_col,      num_cols),              # Internals … last currency col (26+)
    ]
    for first_col, last_col in col_groups:
        # Left and right edges — full height of the data
        for row in range(1, grand_total_row + 1):
            lc = ws.cell(row=row, column=first_col)
            lc.border = Border(left=_MED, right=lc.border.right,
                               top=lc.border.top, bottom=lc.border.bottom)
            rc = ws.cell(row=row, column=last_col)
            rc.border = Border(left=rc.border.left, right=_MED,
                               top=rc.border.top, bottom=rc.border.bottom)
        # Top edge — header row
        for col in range(first_col, last_col + 1):
            tc = ws.cell(row=1, column=col)
            tc.border = Border(left=tc.border.left, right=tc.border.right,
                               top=_MED, bottom=tc.border.bottom)
        # Bottom edge — grand total row
        for col in range(first_col, last_col + 1):
            bc = ws.cell(row=grand_total_row, column=col)
            bc.border = Border(left=bc.border.left, right=bc.border.right,
                               top=bc.border.top, bottom=_MED)

    ws.freeze_panes = "A4"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

# Cross-sheet references to Breakout Budget's pinned Row 2 ("TOTAL")
_BB_GRAND_TOTAL = "='Breakout Budget'!I2"   # col I  (9)  Grand Total
_BB_PROV_LABOUR = "='Breakout Budget'!U2"   # col U  (21) Provincial Labour
_BB_FED_LABOUR  = "='Breakout Budget'!N2"   # col N  (14) Federal Labour
_BB_MEALS       = "='Breakout Budget'!AA2"  # col AA (27) Meals

# Light yellow fill for user-editable input cells
_INPUT_FILL = PatternFill(start_color="FFFDE7", end_color="FFFDE7", fill_type="solid")
_PCT_FORMAT = '0.00%'


def _write_ofttc_sheet(ws, title: str) -> None:
    """Ontario – Full (OFTTC) calculation sheet, linked to Breakout Budget Row 2.

    Layout matches the reference Excel design:
    - Green-fill title block at top
    - Borders ONLY on grey section-header / total rows; data rows borderless
    - Uniform row height throughout
    - Footer summary (Total PC + % of Total Credits) in bold italic
    """
    ws.title = "Ontario - OFTTC"

    ROW_H = 16
    _GFI = _SECTION_HEADER_FILL   # D9D9D9 light grey

    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 16

    # ── low-level helpers ──────────────────────────────────────────
    def _plain(row, col, value=None, font=None, fill=None, align=None, fmt=None):
        """Cell with NO border."""
        ws.row_dimensions[row].height = ROW_H
        c = ws.cell(row=row, column=col, value=value)
        c.font      = font  or _NORMAL
        c.border    = _NO_BORDER
        c.alignment = align or _LEFT
        if fill: c.fill = fill
        if fmt:  c.number_format = fmt
        return c

    def _lined(row, col, value=None, font=None, fill=None, align=None, fmt=None):
        """Cell on a grey row — fill/font only; borders applied in post-processing."""
        ws.row_dimensions[row].height = ROW_H
        c = ws.cell(row=row, column=col, value=value)
        c.font      = font  or _BOLD
        c.border    = _NO_BORDER
        c.fill      = fill or _GFI
        c.alignment = align or _LEFT
        if fmt: c.number_format = fmt
        return c

    # ── row-level helpers ──────────────────────────────────────────
    def blank_row(row):
        for col in range(1, 4):
            _plain(row, col)

    def grey_row(row, label="", c_val=None, c_fmt=_ACCOUNTING_FORMAT):
        _lined(row, 1, label, fill=_GFI)
        _lined(row, 2, fill=_GFI)
        _lined(row, 3, c_val, fill=_GFI, align=_RIGHT, fmt=c_fmt)

    def label_row(row, text, font=None):
        _plain(row, 1, text, font=font or _NORMAL)
        _plain(row, 2)
        _plain(row, 3)

    def data_row(row, label, b_val=None, c_val=None, bold=False,
                 c_fmt=_ACCOUNTING_FORMAT, b_input=False, c_input=False):
        _plain(row, 1, label, font=_BOLD if bold else _NORMAL)
        b = _plain(row, 2, b_val, align=_CENTER)
        if b_input: b.fill = _INPUT_FILL
        c = _plain(row, 3, c_val, font=_BOLD if bold else _NORMAL,
                   align=_RIGHT, fmt=c_fmt)
        if c_input: c.fill = _INPUT_FILL

    # ══════════════════════════════════════════════════════════════
    # Title block
    # ══════════════════════════════════════════════════════════════
    # Row 1: sheet title with green fill
    for col in range(1, 4):
        _plain(1, col, fill=_TITLE_GREEN_FILL)
    _plain(1, 1, "ONTARIO \u2013 FULL (OFTTC)",
           font=_BOLD_ITALIC, fill=_TITLE_GREEN_FILL)

    blank_row(2)

    # Row 3: production name
    _plain(3, 1, title, font=_BOLD)
    _plain(3, 2); _plain(3, 3)

    # Row 4: sub-title
    label_row(4, "Tax Credit Calculation", font=_BOLD)

    blank_row(5)

    # ══════════════════════════════════════════════════════════════
    # ONTARIO PROVINCIAL TAX CREDIT
    # ══════════════════════════════════════════════════════════════
    grey_row(6, "ONTARIO PROVINCIAL TAX CREDIT")
    blank_row(7)
    label_row(8, "A")

    R_PC = 9
    data_row(R_PC, "Total Production Cost", c_val=_BB_GRAND_TOTAL)

    R_ONT_LAB = 10
    data_row(R_ONT_LAB, "Estimate of Total Ont. Labour", c_val=_BB_PROV_LABOUR)

    data_row(11, "Proportion of labour",
             c_val=f"=C{R_ONT_LAB}/C{R_PC}", c_fmt=_PCT_FORMAT)

    blank_row(12)
    label_row(13, "B")
    blank_row(14)

    R_B_LAB = 15
    data_row(R_B_LAB, "Estimate of total Labour expenditure",
             c_val=f"=C{R_ONT_LAB}")

    R_EQUITY = 16; R_DEFS_P = 17; R_OTHERS = 18
    data_row(R_EQUITY, "Reduction", b_val="Equity",    c_input=True)
    data_row(R_DEFS_P, "",          b_val="Deferrals",  c_input=True)
    data_row(R_OTHERS, "",          b_val="Others",     c_input=True)

    blank_row(19)

    R_NET_P = 20
    data_row(R_NET_P, "Net Production cost", bold=True,
             c_val=(f"=C{R_B_LAB}"
                    f"-IF(ISNUMBER(C{R_EQUITY}),C{R_EQUITY},0)"
                    f"-IF(ISNUMBER(C{R_DEFS_P}),C{R_DEFS_P},0)"
                    f"-IF(ISNUMBER(C{R_OTHERS}),C{R_OTHERS},0)"))

    blank_row(21)
    label_row(22, "C")
    blank_row(23)

    R_ONT_LAB_C = 24
    data_row(R_ONT_LAB_C, "Ontario Labour", c_val=f"=C{R_NET_P}")

    R_GENERAL = 25
    data_row(R_GENERAL, "General OFTTC (\u00d735%)", bold=True,
             c_val=f"=C{R_ONT_LAB_C}*0.35")

    blank_row(26)

    R_REGIONAL = 27
    data_row(R_REGIONAL, "Regional Bonus \u2013 10%", bold=True,
             b_val="y", b_input=True,
             c_val=f'=IF(LOWER(B{R_REGIONAL})="y",C{R_ONT_LAB_C}*0.1,0)')

    blank_row(28)

    R_OFTTC = 29
    grey_row(R_OFTTC, "TOTAL OFTTC", c_val=f"=C{R_GENERAL}+C{R_REGIONAL}")

    blank_row(30)

    data_row(31, "Percentage of budget",
             c_val=f"=C{R_OFTTC}/C{R_PC}", c_fmt=_PCT_FORMAT)

    # ══════════════════════════════════════════════════════════════
    # FEDERAL TAX CREDIT
    # ══════════════════════════════════════════════════════════════
    grey_row(32, "FEDERAL TAX CREDIT")
    blank_row(33)
    blank_row(34)

    R_FED_PC = 35
    data_row(R_FED_PC, "Total Production cost", c_val=f"=C{R_PC}")

    blank_row(36)

    R_ON_TAX = 37
    data_row(R_ON_TAX, "ON Tax Credits", c_val=f"=-C{R_OFTTC}")

    R_FED_DEFS = 38
    data_row(R_FED_DEFS, "Deferrals", c_input=True)

    R_ME = 39
    _plain(R_ME, 1, "50% Meals & Entertainment")
    _plain(R_ME, 2, _BB_MEALS, align=_RIGHT, fmt=_ACCOUNTING_FORMAT)
    _plain(R_ME, 3, f"=IF(ISNUMBER(B{R_ME}),-B{R_ME}*0.5,0)",
           align=_RIGHT, fmt=_ACCOUNTING_FORMAT)

    R_ASSIST = 40
    data_row(R_ASSIST, "Assistance", c_input=True)

    R_NET_F = 41
    data_row(R_NET_F, "Net Production Cost", bold=True,
             c_val=(f"=C{R_FED_PC}+C{R_ON_TAX}"
                    f"-IF(ISNUMBER(C{R_FED_DEFS}),C{R_FED_DEFS},0)"
                    f"+C{R_ME}"
                    f"-IF(ISNUMBER(C{R_ASSIST}),C{R_ASSIST},0)"))

    R_ELIG_A = 42
    data_row(R_ELIG_A, "(A) Eligible production cost", bold=True,
             c_val=f"=C{R_NET_F}*0.6")

    blank_row(43)

    R_FED_LAB = 44
    data_row(R_FED_LAB, "Labour expenditure", c_val=_BB_FED_LABOUR)

    blank_row(45)

    R_LAB_DEFS = 46
    data_row(R_LAB_DEFS, "Deferrals", c_input=True)

    R_SUB = 47
    data_row(R_SUB, "Sub-total",
             c_val=(f"=C{R_FED_LAB}"
                    f"-IF(ISNUMBER(C{R_LAB_DEFS}),C{R_LAB_DEFS},0)"))

    R_OWN = 48
    data_row(R_OWN, "Percentage of ownership",
             c_val=1.0, c_input=True, c_fmt="0%")

    R_NET_LAB_B = 49
    data_row(R_NET_LAB_B, "(B) Net labour expenditure", bold=True,
             c_val=f"=C{R_SUB}*C{R_OWN}")

    blank_row(50)

    R_ELIG_FED = 51
    data_row(R_ELIG_FED, "Eligible cost for Fed. Tax Credit", bold=True,
             c_val=f"=MIN(C{R_ELIG_A},C{R_NET_LAB_B})")

    blank_row(52)

    R_FED_CR = 53
    data_row(R_FED_CR, "Total Federal Tax Credit", bold=True,
             c_val=f"=C{R_ELIG_FED}*0.25")

    data_row(54, "Percentage of budget",
             c_val=f"=C{R_FED_CR}/C{R_PC}", c_fmt=_PCT_FORMAT)

    R_TOTAL = 55
    grey_row(R_TOTAL, "TOTAL TAX CREDIT",
             c_val=f"=C{R_OFTTC}+C{R_FED_CR}")

    # ── Post-processing: outline borders ──────────────────────────────
    # Grey rows: 6 (ONTARIO PROV), R_OFTTC (TOTAL OFTTC),
    #            32 (FEDERAL TAX), R_TOTAL (TOTAL TAX CREDIT)
    CALC_START = 6
    CALC_END   = R_TOTAL
    _GREY_ROWS = {CALC_START, R_OFTTC, 32, CALC_END}

    # For every cell in the calculation block, compute its border from
    # two rules:
    #   1. Grey rows   → top + bottom across full width
    #   2. Outer box   → left on col-A, right on col-C, top on first row,
    #                    bottom on last row
    for row in range(CALC_START, CALC_END + 1):
        is_grey  = row in _GREY_ROWS
        is_start = row == CALC_START
        is_end   = row == CALC_END
        for col in range(1, 4):
            ws.cell(row=row, column=col).border = Border(
                top    = _THIN if (is_grey or is_start) else None,
                bottom = _THIN if (is_grey or is_end)   else None,
                left   = _THIN if col == 1               else None,
                right  = _THIN if col == 3               else None,
            )

    blank_row(56)

    # Footer: Total Production Cost + % of Total Tax Credits (bold italic)
    _plain(57, 1, "Total Production Cost", font=_BOLD_ITALIC)
    _plain(57, 2)
    _plain(57, 3, f"=C{R_PC}", font=_BOLD_ITALIC,
           align=_RIGHT, fmt=_ACCOUNTING_FORMAT)

    _plain(58, 1, "Percentage of Total Tax Credits", font=_BOLD_ITALIC)
    _plain(58, 2)
    _plain(58, 3, f"=C{R_TOTAL}/C{R_PC}", font=_BOLD_ITALIC,
           align=_RIGHT, fmt=_PCT_FORMAT)


def write_tax_credit_excel(
    budget: ParsedBudget,
    title: str,
    overrides: dict | None = None,
) -> BytesIO:
    """Build a tax credit filing workbook and return as BytesIO.

    ``overrides`` is an optional dict mapping account_code → BreakoutOverride
    (or any object/dict with the same fields). When provided, these values
    supersede the BREAKOUT_BIBLE for the matching account codes.
    """
    wb = Workbook()

    # Remove the default empty sheet
    default_sheet = wb.active
    wb.remove(default_sheet)

    ws_topsheet = wb.create_sheet("Topsheet")
    _write_topsheet(ws_topsheet, budget, title)

    ws_lines = wb.create_sheet("Budget Lines")
    _write_budget_lines(ws_lines, budget)

    ws_detail = wb.create_sheet("Detail Budget")
    _write_detail_budget(ws_detail, budget)

    ws_breakout = wb.create_sheet("Breakout Budget")
    _write_breakout_budget(ws_breakout, budget, overrides or {})

    ws_ofttc = wb.create_sheet("Ontario - OFTTC")
    _write_ofttc_sheet(ws_ofttc, title)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
