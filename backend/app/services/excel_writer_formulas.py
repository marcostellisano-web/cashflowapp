"""Formula-based cashflow Excel workbook generator.

Produces the standard workbook plus a "Timing" sheet with one editable row
per timing pattern from the Cashflow Timing Bible.  Patterns and titles match
exactly what the Distribution tab of the website shows.

Each Timing row contains 0/1 values across every week column, computed by
running the authoritative bible_distributor logic for that pattern.

Cashflow column D holds the editable Pattern name.  Weekly cells (E+) use:
    =IFERROR(
      $C{row}
      * INDEX(Timing!{col}$6:{col}$41, MATCH($D{row}, Timing!$A$6:$A$41, 0))
      / SUM(OFFSET(Timing!$D$6, MATCH($D{row}, Timing!$A$6:$A$41, 0)-1, 0, 1, {n}))
    , 0)

Editing cell D or copy-pasting a pattern name from another row instantly
re-routes the entire row's weekly distribution.
"""

from __future__ import annotations

import re
from io import BytesIO

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import column_index_from_string, get_column_letter

from app.domain.timing_bible_data import DEFAULT_BIBLE
from app.models.budget import ParsedBudget
from app.models.cashflow import CashflowOutput
from app.models.distribution import LineItemDistribution, PhaseAssignment
from app.models.production import ProductionParameters
from app.models.timing_bible import BibleEntry, TimingPattern
from app.services.bible_distributor import distribute_bible_entry
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

# ── TimingPattern → human-readable title ─────────────────────────────────────
# These titles match what is shown in the Distribution tab of the website.

_TIMING_PATTERN_TITLE: dict[TimingPattern, str] = {
    TimingPattern.FULL_PAYROLL:                  "Full Payroll",
    TimingPattern.PREP_TO_FIRST_SHOOT_PAYROLL:   "Prep to First Shoot",
    TimingPattern.PREP_TO_LAST_SHOOT_PAYROLL:    "Prep to Last Shoot",
    TimingPattern.PREP_TO_DELIVERY_PAYROLL:      "Prep to Delivery Payroll",
    TimingPattern.PREP_TO_ROUGH_CUT_PAYROLL:     "Prep to Rough Cut",
    TimingPattern.PP_MINUS_2_TO_DELIVERY_PAYROLL: "PP -2 to Delivery Payroll",
    TimingPattern.PP_MINUS_1_TO_DELIVERY_PAYROLL: "PP -1 to Delivery Payroll",
    TimingPattern.PP_TO_END:                     "PP to End",
    TimingPattern.SHOOT_PAYROLL:                 "Shoot Payroll",
    TimingPattern.EDIT_MINUS_2_TO_PIC_LOCK:      "Edit -2 to Picture Lock",
    TimingPattern.EDIT_PAYROLL:                  "Edit Payroll",
    TimingPattern.ARCHIVE_RESEARCH:              "Archive Research",
    TimingPattern.NARRATOR:                      "Narrator",
    TimingPattern.CASTING:                       "Casting",
    TimingPattern.STILL_PHOTO:                   "Still Photo",
    TimingPattern.ONLINE_EDITOR:                 "Online Editor",
    TimingPattern.COMPOSER:                      "Composer",
    TimingPattern.FULL_AP:                       "Full AP",
    TimingPattern.PREP_TO_DELIVERY_AP:           "Prep to Delivery AP",
    TimingPattern.INTERNALS:                     "Internals",
    TimingPattern.EDIT_INTERNALS:                "Edit Internals",
    TimingPattern.TRAVEL:                        "Travel",
    TimingPattern.PER_DIEM:                      "Per Diem",
    TimingPattern.SHOOT_PURCHASES:               "Shoot Purchases",
    TimingPattern.SHOOT_RENTALS:                 "Shoot Rentals",
    TimingPattern.MONTHLY_SHOOT:                 "Monthly (shoot months)",
    TimingPattern.PRE_SHOOT:                     "Pre-Shoot",
    TimingPattern.LEGAL:                         "Legal",
    TimingPattern.PICK_LOCK:                     "Pick Lock",
    TimingPattern.DELIVERY_COPIES:               "Delivery Copies",
    TimingPattern.MIX:                           "Mix",
    TimingPattern.AFTER_DELIVERY:                "After Delivery",
    TimingPattern.GRAPHICS:                      "Graphics",
    TimingPattern.INSURANCE:                     "Insurance",
    TimingPattern.FINANCING:                     "Financing",
    TimingPattern.MID_EDIT_LUMP:                 "Mid Edit Lump",
}

# Reverse map: title string → TimingPattern (used when computing patterns)
_TITLE_TIMING_PATTERN: dict[str, TimingPattern] = {
    v: k for k, v in _TIMING_PATTERN_TITLE.items()
}

# Ordered list: all timing patterns in a logical display order for the Timing sheet
ALL_TIMING_TITLES: list[str] = list(_TIMING_PATTERN_TITLE.values())

# Descriptions shown in col B of the Timing sheet
_TIMING_DESCRIPTIONS: dict[str, str] = {
    "Full Payroll":                "Payroll weeks — full span (prep through final delivery)",
    "Prep to First Shoot":         "Payroll weeks from prep start through end of first shoot block",
    "Prep to Last Shoot":          "Payroll weeks from prep start through end of last shoot block",
    "Prep to Delivery Payroll":    "Payroll weeks from prep start through final delivery",
    "Prep to Rough Cut":           "Payroll weeks from prep start through final rough cut",
    "PP -2 to Delivery Payroll":   "Payroll from 2 weeks before PP start through final delivery",
    "PP -1 to Delivery Payroll":   "Payroll from 1 week before PP start through final delivery",
    "PP to End":                   "Payroll weeks from PP start through final delivery",
    "Shoot Payroll":               "Payroll weeks during each shooting block",
    "Edit -2 to Picture Lock":     "Payroll from 2 weeks before edit start through final picture lock",
    "Edit Payroll":                "Payroll weeks from edit start through final picture lock",
    "Archive Research":            "Payroll weeks over the edit period",
    "Narrator":                    "Payroll weeks from 3-4 weeks after edit start through final picture lock",
    "Casting":                     "Two payroll weeks: 4 and 2 weeks before PP start",
    "Still Photo":                 "Payroll week ~2-3 weeks after each shooting block ends",
    "Online Editor":               "Payroll weeks ~2-3 weeks after each episode online date",
    "Composer":                    "Two payroll weeks: midpoint of edit + near final picture lock",
    "Full AP":                     "AP weeks — full span (prep through final delivery)",
    "Prep to Delivery AP":         "AP weeks from prep start through final delivery",
    "Internals":                   "Monthly mid-month AP weeks — prep through delivery",
    "Edit Internals":              "Monthly mid-month AP weeks during the edit period",
    "Travel":                      "AP week ~2-3 weeks before each shoot block",
    "Per Diem":                    "AP weeks during each shoot block (per diems / catering)",
    "Shoot Purchases":             "AP weeks during each shoot block",
    "Shoot Rentals":               "AP weeks during each shooting block",
    "Monthly (shoot months)":      "Last AP week of each calendar month during the shoot",
    "Pre-Shoot":                   "AP week ~2-3 weeks before Principal Photography starts",
    "Legal":                       "4 AP weeks spread evenly from prep start to final delivery",
    "Pick Lock":                   "AP week ~2-3 weeks after each episode picture lock",
    "Delivery Copies":             "AP week ~2-3 weeks before each episode delivery",
    "Mix":                         "AP week ~2-3 weeks after each episode mix date",
    "After Delivery":              "AP week ~4 weeks after final delivery",
    "Graphics":                    "Bi-weekly AP weeks from edit start through final online",
    "Insurance":                   "AP week ~2-3 weeks after prep start",
    "Financing":                   "AP week nearest to September 30, pro-rated by total spend in each fiscal year (Nov 1–Oct 31)",
    "Mid Edit Lump":               "Single AP lump sum at the midpoint of the edit period",
}

# Phase-assignment fallback (for codes not in the bible and no override set)
_PHASE_FALLBACK_PATTERN: dict[PhaseAssignment, TimingPattern] = {
    PhaseAssignment.PREP:               TimingPattern.INTERNALS,
    PhaseAssignment.PRODUCTION:         TimingPattern.SHOOT_PAYROLL,
    PhaseAssignment.POST:               TimingPattern.EDIT_PAYROLL,
    PhaseAssignment.DELIVERY:           TimingPattern.AFTER_DELIVERY,
    PhaseAssignment.FULL_SPAN:          TimingPattern.FULL_PAYROLL,
    PhaseAssignment.PREP_AND_PRODUCTION: TimingPattern.FULL_PAYROLL,
    PhaseAssignment.PRODUCTION_AND_POST: TimingPattern.EDIT_PAYROLL,
}

# Fills for the Timing sheet
_ACTIVE_FILL   = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")
_INACTIVE_FILL = PatternFill(start_color="FFFDE7", end_color="FFFDE7", fill_type="solid")
_HEADER_FILL   = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")

_TIMING_SHEET = "Timing"

# Formula-version Cashflow layout:
#   A: Code  B: Description  C: Budget (value)  D: Pattern (editable)  E+: weekly formulas
_PATTERN_COL        = FIRST_WEEK_COL          # D (col 4)
_FML_FIRST_WEEK_COL = FIRST_WEEK_COL + 1      # E (col 5)

# Timing sheet data rows: 6 through 6+36-1 = 41 (one row per TimingPattern)
_TIMING_DATA_END = DATA_START_ROW + len(ALL_TIMING_TITLES) - 1


# ── Lookup helpers ────────────────────────────────────────────────────────────

def _get_pattern_for_dist(dist: LineItemDistribution) -> tuple[str, TimingPattern]:
    """Return (timing_title, TimingPattern) for a LineItemDistribution.

    Priority:
      1. dist.timing_pattern_override  (set by Distribution tab / timing bible)
      2. DEFAULT_BIBLE entry for the code
      3. PhaseAssignment fallback
    """
    if dist.timing_pattern_override:
        try:
            tp = TimingPattern(dist.timing_pattern_override)
            return _TIMING_PATTERN_TITLE.get(tp, tp.value), tp
        except ValueError:
            pass

    entry = DEFAULT_BIBLE.get_entry(dist.budget_code)
    if entry:
        title = _TIMING_PATTERN_TITLE.get(entry.timing_pattern, entry.timing_title)
        return title, entry.timing_pattern

    tp = _PHASE_FALLBACK_PATTERN.get(dist.phase, TimingPattern.FULL_PAYROLL)
    return _TIMING_PATTERN_TITLE.get(tp, "Full Payroll"), tp


# ── Pattern computation ───────────────────────────────────────────────────────

def _compute_timing_patterns(
    title_to_tp: dict[str, TimingPattern],
    output: CashflowOutput,
    params: ProductionParameters,
) -> dict[str, list[float]]:
    """Compute patterns for each timing title using the authoritative
    bible_distributor implementation.

    Most patterns return 0/1 values (inactive/active weeks).
    FINANCING returns proportional float weights (e.g. 0.65 / 0.35 across two
    fiscal years), computed from actual spend in output.weekly_totals so that
    the Timing sheet correctly splits the financing budget by FY spend.
    """
    patterns: dict[str, list[float]] = {}
    for title, tp in title_to_tp.items():
        dummy = BibleEntry(
            account_code="0000",
            description="",
            timing_pattern=tp,
            timing_details="",
            timing_title=title,
        )
        try:
            if tp == TimingPattern.FINANCING:
                # Use spend-based pro-ration from the Python output
                ctx = {"weekly_spend": list(output.weekly_totals)}
                weights = distribute_bible_entry(1.0, dummy, output.weeks, params, context=ctx)
                patterns[title] = [round(float(w), 4) for w in weights]
            else:
                weights = distribute_bible_entry(1.0, dummy, output.weeks, params)
                patterns[title] = [1.0 if w > 1e-9 else 0.0 for w in weights]
        except Exception:
            patterns[title] = [0.0] * len(output.weeks)
    return patterns


# ── Timing sheet writer ───────────────────────────────────────────────────────

def _write_timing_sheet(
    wb,
    output: CashflowOutput,
    params: ProductionParameters,
    title_to_row: dict[str, int],
    title_to_tp: dict[str, TimingPattern],
) -> None:
    """Create the 'Timing' sheet with one pattern row per timing category."""
    ws = wb.create_sheet(_TIMING_SHEET, 1)
    weeks = output.weeks
    num_weeks = len(weeks)
    last_col = FIRST_WEEK_COL + num_weeks - 1
    first_col_letter = get_column_letter(FIRST_WEEK_COL)
    last_col_letter = get_column_letter(last_col)

    patterns = _compute_timing_patterns(title_to_tp, output, params)

    # ── Row 1: title ──────────────────────────────────────────────────────────
    ws.cell(row=1, column=1, value="Distribution Timing Patterns").font = TITLE_FONT

    # ── Row 2: instructions ───────────────────────────────────────────────────
    ws.cell(
        row=2, column=1,
        value=(
            "Edit 0 / 1 values in the week columns to change when a cost is distributed.  "
            "Green = active (1), yellow = inactive (0).  "
            "Pattern names match the Distribution tab — copy any name into col D of Cashflow "
            "to re-route that line item."
        ),
    ).font = Font(name="Calibri", italic=True, size=9, color="555555")

    # ── Row 3: column A/B headers + phase labels live-linked from Cashflow ────
    for col_idx, label in ((1, "Timing Pattern"), (2, "Description")):
        cell = ws.cell(row=3, column=col_idx, value=label)
        cell.font = HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.border = THIN_BORDER

    for i, week in enumerate(weeks):
        col = FIRST_WEEK_COL + i
        col_letter = get_column_letter(col)
        # After insert_cols in Cashflow, week i is now at _FML_FIRST_WEEK_COL+i in Cashflow.
        # _shift_cashflow_col_refs will update these refs from D→E etc.
        cell = ws.cell(row=3, column=col, value=f"=Cashflow!{col_letter}4")
        cell.font = Font(name="Calibri", bold=True, size=8)
        cell.fill = _get_phase_fill(week.phase_label)
        cell.alignment = Alignment(horizontal="center", text_rotation=90)
        cell.border = THIN_BORDER

    # ── Row 4: week dates live-linked from Cashflow ───────────────────────────
    ws.cell(row=4, column=1, value="Week commencing →").font = Font(
        name="Calibri", italic=True, size=8, color="888888"
    )
    for i in range(num_weeks):
        col = FIRST_WEEK_COL + i
        col_letter = get_column_letter(col)
        cell = ws.cell(row=4, column=col, value=f"=Cashflow!{col_letter}5")
        cell.font = Font(name="Calibri", size=7)
        cell.number_format = "DD-MMM"
        cell.alignment = Alignment(horizontal="center")
        cell.border = THIN_BORDER

    # ── Pattern rows ──────────────────────────────────────────────────────────
    for title, excel_row in title_to_row.items():
        pat = patterns.get(title, [0] * num_weeks)

        label_cell = ws.cell(row=excel_row, column=1, value=title)
        label_cell.font = Font(name="Calibri", bold=True, size=10)
        label_cell.border = THIN_BORDER

        desc_cell = ws.cell(
            row=excel_row, column=2,
            value=_TIMING_DESCRIPTIONS.get(title, title),
        )
        desc_cell.font = Font(name="Calibri", size=9, italic=True, color="444444")
        desc_cell.border = THIN_BORDER

        # Detect proportional rows (Financing): any value is not exactly 0 or 1
        is_proportional = any(0 < v < 0.999 for v in pat)
        for i, val in enumerate(pat):
            col = FIRST_WEEK_COL + i
            cell = ws.cell(row=excel_row, column=col, value=val)
            cell.number_format = "0.00" if is_proportional else "0"
            cell.alignment = Alignment(horizontal="center")
            cell.border = THIN_BORDER
            is_active = val > 1e-9
            cell.fill = _ACTIVE_FILL if is_active else _INACTIVE_FILL
            cell.font = Font(
                name="Calibri", bold=is_active, size=9,
                color="1B5E20" if is_active else "BBBBBB",
            )

    # ── Column widths ─────────────────────────────────────────────────────────
    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 52
    for i in range(num_weeks):
        ws.column_dimensions[get_column_letter(FIRST_WEEK_COL + i)].width = 5

    ws.freeze_panes = ws.cell(row=DATA_START_ROW, column=FIRST_WEEK_COL)


# ── Cross-sheet column-reference fixer ───────────────────────────────────────

def _shift_cashflow_col_refs(wb, min_col_idx: int) -> None:
    """After inserting a column at min_col_idx in Cashflow, shift all Cashflow!
    column references with col_idx >= min_col_idx by +1 in every other sheet.

    openpyxl adjusts intra-sheet refs on insert_cols but NOT cross-sheet refs.
    """
    skip = {"Cashflow"}
    max_idx = wb["Cashflow"].max_column + 10

    for ws in wb.worksheets:
        if ws.title in skip:
            continue
        for row in ws.iter_rows():
            for cell in row:
                v = cell.value
                if not isinstance(v, str) or "Cashflow!" not in v:
                    continue
                formula = v
                for ci in range(max_idx, min_col_idx - 1, -1):
                    old = get_column_letter(ci)
                    new = get_column_letter(ci + 1)
                    oe = re.escape(old)
                    # Whole-column range: Cashflow!D:D / Cashflow!$D:$D
                    formula = re.sub(
                        r"(?i)(Cashflow!\$?)(" + oe + r")(:\$?)(" + oe + r")",
                        lambda m, n=new: m.group(1) + n + m.group(3) + n,
                        formula,
                    )
                    # Cell ref: Cashflow!D4 / Cashflow!$D4 / Cashflow!$D$4
                    formula = re.sub(
                        r"(?i)(Cashflow!\$?)(" + oe + r")(?=\$?\d)",
                        lambda m, n=new: m.group(1) + n,
                        formula,
                    )
                if formula != v:
                    cell.value = formula


# ── Main entry point ──────────────────────────────────────────────────────────

def write_formula_cashflow_excel(
    output: CashflowOutput,
    params: ProductionParameters,
    distributions: list[LineItemDistribution],
    budget: ParsedBudget | None = None,
) -> BytesIO:
    """Generate a formula-driven cashflow workbook with an editable Timing sheet.

    Layout (formula version):
      A: Code  B: Description  C: Budget (plain value)
      D: Pattern (editable — matches Distribution tab exactly, drives weekly formulas)
      E+: =IFERROR($C{r}*INDEX(Timing…,MATCH($D{r},…))/SUM(OFFSET(…)),0)

    Pattern names in col D are the same titles shown in the Distribution tab.
    Copy-paste any name from Timing!$A to re-route a line item's distribution.
    """
    # ── 1. Standard workbook ──────────────────────────────────────────────────
    standard_buf = write_cashflow_excel(output, params, budget=budget)
    wb = load_workbook(standard_buf)
    ws = wb["Cashflow"]

    # ── 2. Build per-row timing info from actual distributions ─────────────────
    dist_by_code: dict[str, LineItemDistribution] = {
        d.budget_code: d for d in distributions
    }

    # Fixed row mapping: all 36 patterns always present in Timing sheet
    title_to_row: dict[str, int] = {
        title: DATA_START_ROW + i
        for i, title in enumerate(ALL_TIMING_TITLES)
    }
    title_to_tp: dict[str, TimingPattern] = {
        title: _TITLE_TIMING_PATTERN[title]
        for title in ALL_TIMING_TITLES
    }

    row_titles: list[str] = []
    for row_data in output.rows:
        dist = dist_by_code.get(row_data.code)
        if dist is None:
            # Code not in distributions — use phase fallback
            tp = TimingPattern.FULL_PAYROLL
            title = _TIMING_PATTERN_TITLE[tp]
        else:
            title, tp = _get_pattern_for_dist(dist)
        # If the title isn't in our fixed list (edge case), add it
        if title not in title_to_row:
            title_to_row[title] = DATA_START_ROW + len(title_to_row)
            title_to_tp[title] = tp
        row_titles.append(title)

    # ── 3. Create Timing sheet ────────────────────────────────────────────────
    _write_timing_sheet(wb, output, params, title_to_row, title_to_tp)

    # ── 4. Insert Pattern column at D in Cashflow, shifting weeks to E+ ───────
    ws.insert_cols(_PATTERN_COL)
    # Fix cross-sheet Cashflow! refs in all other sheets (incl. Timing row 3/4 headers)
    _shift_cashflow_col_refs(wb, _PATTERN_COL)

    num_weeks = len(output.weeks)
    tds = DATA_START_ROW      # first timing data row
    tde = _TIMING_DATA_END    # last  timing data row
    t_first_col = get_column_letter(FIRST_WEEK_COL)  # "D" — Timing weeks start at D

    # ── 5. Pattern column header (D5) ─────────────────────────────────────────
    phdr = ws.cell(row=5, column=_PATTERN_COL, value="Pattern")
    phdr.font = Font(name="Calibri", bold=True, size=9, color="1565C0")
    phdr.alignment = Alignment(horizontal="center", wrap_text=False)
    phdr.border = THIN_BORDER
    ws.column_dimensions[get_column_letter(_PATTERN_COL)].width = 22

    # Rename "Total" header → "Budget"
    ws.cell(row=5, column=TOTAL_COL).value = "Budget"

    # ── 6. Rewrite data rows ──────────────────────────────────────────────────
    for row_idx, (row_data, title) in enumerate(zip(output.rows, row_titles)):
        excel_row = DATA_START_ROW + row_idx

        # Col C: budget as plain value (avoids circular ref — weekly cells ref $C{r})
        total_cell = ws.cell(row=excel_row, column=TOTAL_COL)
        total_cell.value = round(row_data.total, 2)
        total_cell.number_format = CURRENCY_FORMAT
        total_cell.font = Font(name="Calibri", size=10, bold=True)

        # Col D: Pattern name — editable; changing it re-routes all weekly formulas
        pcell = ws.cell(row=excel_row, column=_PATTERN_COL, value=title)
        pcell.font = Font(name="Calibri", size=9, italic=True, color="1565C0")
        pcell.alignment = Alignment(horizontal="center")
        pcell.border = THIN_BORDER

        # Cols E+: formula reads pattern from $D{row} via MATCH into Timing sheet
        # Timing week columns are always D, E, F, … (FIRST_WEEK_COL + offset)
        # Cashflow week columns are E, F, G, … (_FML_FIRST_WEEK_COL + offset)
        for col_offset in range(num_weeks):
            t_wcol = get_column_letter(FIRST_WEEK_COL + col_offset)  # Timing col
            cf_col = _FML_FIRST_WEEK_COL + col_offset                 # Cashflow col

            formula = (
                f"=IFERROR("
                f"$C{excel_row}"
                f"*INDEX(Timing!{t_wcol}${tds}:{t_wcol}${tde},"
                f"MATCH($D{excel_row},Timing!$A${tds}:$A${tde},0))"
                f"/SUM(OFFSET(Timing!${t_first_col}${tds},"
                f"MATCH($D{excel_row},Timing!$A${tds}:$A${tde},0)-1,"
                f"0,1,{num_weeks}))"
                f",0)"
            )
            cell = ws.cell(row=excel_row, column=cf_col)
            cell.value = formula
            cell.number_format = CURRENCY_FORMAT

    # Freeze: columns A–D always visible, rows 1–5 always visible
    ws.freeze_panes = ws.cell(row=DATA_START_ROW, column=_FML_FIRST_WEEK_COL)

    # ── 7. Save ───────────────────────────────────────────────────────────────
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
