"""Generate a formatted Tax Credit Filing Budget Excel workbook from a ParsedBudget."""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.models.budget import ParsedBudget

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------
CURRENCY_FORMAT = '#,##0'

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


def _write_breakout_budget(ws, budget: ParsedBudget) -> None:
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

    Dynamic columns (J onward):
      One "XXX Grand Total" column per distinct currency found in the data.
      Each data row fills its matching currency column with =I{row}; others are 0.

    Final dynamic column:
      Internals – shows =I{row} for rows whose Group (col E) is "Internal OH", else 0.
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

    # Column indices for each currency grand-total column (1-based)
    # Fixed columns A-I = 1-9; currency columns start at 10
    currency_col_map: dict[str, int] = {
        cur: 9 + i + 1 for i, cur in enumerate(seen_currencies)
    }

    # "Internals" column comes after all currency columns
    internals_col: int = 9 + len(seen_currencies) + 1

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
    ] + [f"{cur} Grand Total" for cur in seen_currencies] + ["Internals"]

    num_cols = len(headers)
    widths = [12, 34, 40, 8, 28, 10, 14, 14, 14] + [16] * len(seen_currencies) + [16]

    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width

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
    row_idx = 2
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
            c.number_format = CURRENCY_FORMAT

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
            c.number_format = CURRENCY_FORMAT

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
        c.number_format = CURRENCY_FORMAT

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

        # Section header (merged across all columns)
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=num_cols)
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
                (detail.subtotal,    _RIGHT,  CURRENCY_FORMAT),
                (f"={subtotal_col}*{agg_col}" if is_fringes_row else 0, _RIGHT, CURRENCY_FORMAT),
                (f"=G{row_idx}+H{row_idx}", _RIGHT, CURRENCY_FORMAT),
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
                c.number_format = CURRENCY_FORMAT

            # Internals column: =I{row} if group is "Internal OH", else 0
            internals_value = f"=I{row_idx}" if group_label.strip() == "Internal OH" else 0
            c = ws.cell(row=row_idx, column=internals_col, value=internals_value)
            c.font = _NORMAL
            c.border = _NO_BORDER
            c.alignment = _RIGHT
            c.number_format = CURRENCY_FORMAT

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
            c.number_format = CURRENCY_FORMAT

        # Currency grand total columns for this section total
        for cur, col in currency_col_map.items():
            letter = get_column_letter(col)
            formula = f"=SUM({letter}{section_detail_start}:{letter}{section_detail_end})"
            c = ws.cell(row=row_idx, column=col, value=formula)
            c.font = _BOLD
            c.alignment = _RIGHT
            c.fill = _LIGHT_GRAY_FILL
            c.number_format = CURRENCY_FORMAT

        # Internals column for this section total
        internals_letter = get_column_letter(internals_col)
        formula = f"=SUM({internals_letter}{section_detail_start}:{internals_letter}{section_detail_end})"
        c = ws.cell(row=row_idx, column=internals_col, value=formula)
        c.font = _BOLD
        c.alignment = _RIGHT
        c.fill = _LIGHT_GRAY_FILL
        c.number_format = CURRENCY_FORMAT

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
            c.number_format = CURRENCY_FORMAT
        for cur, col in currency_col_map.items():
            letter = get_column_letter(col)
            refs = ",".join(f"{letter}{r}" for r in all_section_rows)
            c = ws.cell(row=row_idx, column=col, value=f"=SUM({refs})")
            c.font = _WHITE_BOLD
            c.alignment = _RIGHT
            c.fill = _GRAND_TOTAL_FILL
            c.number_format = CURRENCY_FORMAT
        # Internals column for grand total
        internals_letter = get_column_letter(internals_col)
        refs = ",".join(f"{internals_letter}{r}" for r in all_section_rows)
        c = ws.cell(row=row_idx, column=internals_col, value=f"=SUM({refs})")
        c.font = _WHITE_BOLD
        c.alignment = _RIGHT
        c.fill = _GRAND_TOTAL_FILL
        c.number_format = CURRENCY_FORMAT
    else:
        for col in range(7, num_cols + 1):
            c = ws.cell(row=row_idx, column=col, value=0)
            c.font = _WHITE_BOLD
            c.alignment = _RIGHT
            c.fill = _GRAND_TOTAL_FILL
            c.number_format = CURRENCY_FORMAT

    for col in range(1, num_cols + 1):
        ws.cell(row=row_idx, column=col).border = _THIN_BORDER

    ws.freeze_panes = "A2"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def write_tax_credit_excel(budget: ParsedBudget, title: str) -> BytesIO:
    """Build a tax credit filing workbook and return as BytesIO."""
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
    _write_breakout_budget(ws_breakout, budget)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
