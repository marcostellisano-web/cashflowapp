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
    wb = openpyxl.load_workbook(output, data_only=True)

    assert "Detail Budget" in wb.sheetnames
    ws = wb["Detail Budget"]

    values = [row for row in ws.iter_rows(min_row=1, max_col=11, values_only=True)]
    flat_values = [v for row in values for v in row if isinstance(v, str)]

    assert any("02.00" in v for v in flat_values)
    assert any("03.00" in v for v in flat_values)
    assert "Should skip" not in flat_values

    total_values = [row[10] for row in values if isinstance(row[0], str) and "TOTAL" in row[0]]
    assert 1000 in total_values
    assert 500 in total_values
