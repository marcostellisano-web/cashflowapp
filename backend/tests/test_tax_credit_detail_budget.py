from io import BytesIO

import openpyxl

from app.models.budget import BudgetCategory, BudgetDetailRow, BudgetLineItem, ParsedBudget
from app.services.excel_parser import parse_budget_excel
from app.services.tax_credit_writer import write_tax_credit_excel


def test_parse_budget_excel_reads_account_details_rows():
    wb = openpyxl.Workbook()
    ws_categories = wb.active
    ws_categories.title = "Categories"
    ws_categories.append(["Account", "Description", "Total"])
    ws_categories.append(["0201", "Writer(s)", 1000])

    ws_details = wb.create_sheet("Account Details")
    ws_details.append(["Account", "Description", "Amount", "Unit", "x", "Unit 2", "Currency", "Rate", "Unit 3", "Subtotal"])
    ws_details.append(["0201", "Script fee", 2, "wk", "x", 1, "CAD", 500, "ep", 1000])
    ws_details.append(["0201", "Zero row", 1, "wk", "x", 1, "CAD", 0, "ep", 0])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    parsed = parse_budget_excel(buf, filename="test.xlsx")

    assert len(parsed.detail_rows) == 1
    assert parsed.detail_rows[0].account == "0201"
    assert parsed.detail_rows[0].description == "Script fee"
    assert parsed.detail_rows[0].subtotal == 1000


def test_tax_credit_workbook_contains_detail_budget_tab_with_group_totals():
    budget = ParsedBudget(
        line_items=[
            BudgetLineItem(code="0201", description="Writer(s)", total=1000, category=BudgetCategory.ABOVE_THE_LINE),
            BudgetLineItem(code="0301", description="Development", total=500, category=BudgetCategory.ABOVE_THE_LINE),
        ],
        total_budget=1500,
        source_filename="test.xlsx",
        topsheet_totals={"0200": 1000, "0300": 500},
        detail_rows=[
            BudgetDetailRow(account="0201", description="Writer fee", amount=1, unit="wk", unit2="1", currency="CAD", rate=1000, unit3="ep", subtotal=1000),
            BudgetDetailRow(account="0301", description="Script edit", amount=1, unit="wk", unit2="1", currency="CAD", rate=500, unit3="ep", subtotal=500),
            BudgetDetailRow(account="0301", description="Should skip", subtotal=0),
        ],
    )

    output = write_tax_credit_excel(budget, "Test")
    wb = openpyxl.load_workbook(output, data_only=False)

    assert "Detail Budget" in wb.sheetnames
    ws = wb["Detail Budget"]

    values = [row for row in ws.iter_rows(min_row=1, max_col=11, values_only=True)]
    flat_values = [v for row in values for v in row if isinstance(v, str)]

    assert any("02.00" in v for v in flat_values)
    assert any("03.00" in v for v in flat_values)
    assert "Should skip" not in flat_values

    row_0200_total = next(i for i, row in enumerate(values, start=1) if row[0] == "02.00 TOTAL")
    row_0300_total = next(i for i, row in enumerate(values, start=1) if row[0] == "03.00 TOTAL")
    assert values[row_0200_total - 1][10] == f"=SUM(K{row_0200_total - 1}:K{row_0200_total - 1})"
    assert values[row_0300_total - 1][10] == f"=SUM(K{row_0300_total - 1}:K{row_0300_total - 1})"

    total_a_row = next(i for i, row in enumerate(values, start=1) if row[0] == "TOTAL \"A\" – ABOVE THE LINE")
    total_a_formula = values[total_a_row - 1][10]
    assert total_a_formula == f"=SUM(K{row_0200_total},K{row_0300_total})"

    # Columns A/B/C should be left-justified for detail rows
    assert ws["A3"].alignment.horizontal == "left"
    assert ws["B3"].alignment.horizontal == "left"
    assert ws["C3"].alignment.horizontal == "left"

    # Group totals are inserted after their section groups and use formulas
    assert any(v == 'TOTAL "A" – ABOVE THE LINE' for v in flat_values)
    assert any(v == 'TOTAL PRODUCTION "B"' for v in flat_values)
    assert any(v == 'TOTAL POST-PRODUCTION "C"' for v in flat_values)
    assert any(v == 'TOTAL OTHER "D"' for v in flat_values)

    section_03_total_row = next(i for i, row in enumerate(values, start=1) if row[0] == "03.00 TOTAL")
    assert total_a_row == section_03_total_row + 2

    # Interior data cells are unbordered; only section outlines are bordered
    assert ws["B3"].border.left is None or ws["B3"].border.left.style is None
    assert ws["B3"].border.right is None or ws["B3"].border.right.style is None
    assert ws["A2"].border.left.style == "thin"
    assert ws["K3"].border.right.style == "thin"

    # Header row uses light gray fill with only an outer box border
    assert ws["A1"].fill.fgColor.rgb == "00F2F2F2"
    assert ws["B1"].fill.fgColor.rgb == "00F2F2F2"
    assert ws["A1"].border.left.style == "thin"
    assert ws["B1"].border.left is None or ws["B1"].border.left.style is None
    assert ws["B1"].border.right is None or ws["B1"].border.right.style is None
    assert ws["K1"].border.right.style == "thin"


def test_tax_credit_workbook_bible_drives_breakout_basis_columns():
    budget = ParsedBudget(
        line_items=[
            BudgetLineItem(
                code="0201",
                description="Writer(s)",
                total=1000,
                category=BudgetCategory.ABOVE_THE_LINE,
            ),
        ],
        total_budget=1000,
        source_filename="test.xlsx",
        detail_rows=[
            BudgetDetailRow(
                account="0201",
                description="Writer fee",
                currency="CAD",
                subtotal=1000,
            ),
        ],
    )
    overrides = {
        "0201": {
            "is_foreign": None,
            "is_non_prov": True,
            "prov_labour_pct": 0.8,
            "fed_labour_pct": 0.85,
            "prov_svc_labour_pct": 0.7,
            "svc_property_pct": 0.1,
            "fed_svc_labour_pct": 0.75,
        }
    }

    output = write_tax_credit_excel(budget, "Test", overrides=overrides)
    wb = openpyxl.load_workbook(output, data_only=False)

    assert "Breakout Bible" in wb.sheetnames
    bible = wb["Breakout Bible"]
    bible_row = next(row for row in range(5, bible.max_row + 1) if bible.cell(row, 1).value == "0201")
    assert [bible.cell(bible_row, col).value for col in range(3, 9)] == [
        "OUT", 0.8, 0.85, 0.7, 0.1, 0.75,
    ]

    breakout = wb["Breakout Budget"]
    detail_row = next(
        row
        for row in range(1, breakout.max_row + 1)
        if breakout.cell(row, 1).value == "0201" and breakout.cell(row, 3).value == "Writer fee"
    )
    expected_refs = {
        25: "C",  # OUT / Non-Prov
        28: "D",  # Prov Labour %
        21: "E",  # Fed Labour %
        30: "F",  # Prov Svc Labour %
        31: "G",  # Svc Property %
        23: "H",  # Fed Svc Labour %
    }
    for breakout_col, bible_col in expected_refs.items():
        assert breakout.cell(detail_row, breakout_col).value == (
            f'=IF(\'Breakout Bible\'!{bible_col}{bible_row}="","",'
            f"'Breakout Bible'!{bible_col}{bible_row})"
        )
