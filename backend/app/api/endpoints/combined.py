from io import BytesIO

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.api.endpoints.tax_credit import BreakoutOverride, _load_global_bible
from app.database import get_db
from app.models.budget import ParsedBudget
from app.models.cashflow import GenerateRequest
from app.models.distribution import LineItemDistribution
from app.models.production import ProductionParameters
from app.services.cashflow_engine import generate_cashflow
from app.services.excel_writer import populate_cashflow_workbook
from app.services.tax_credit_writer import populate_tax_credit_workbook
from pydantic import BaseModel

router = APIRouter()


class CombinedRequest(BaseModel):
    budget: ParsedBudget
    parameters: ProductionParameters
    distributions: list[LineItemDistribution]
    title: str = ""
    overrides: list[BreakoutOverride] | None = None


@router.post("/combined/generate")
async def generate_combined_excel(
    request: CombinedRequest,
    db: Session = Depends(get_db),
):
    cashflow_output = generate_cashflow(
        budget=request.budget,
        parameters=request.parameters,
        distributions=request.distributions,
    )

    overrides_map = {ov.account_code: ov for ov in (request.overrides or [])}
    global_bible = _load_global_bible(db)
    title = request.title or request.parameters.title

    wb = Workbook()
    wb.remove(wb.active)

    populate_cashflow_workbook(wb, cashflow_output, request.parameters)
    populate_tax_credit_workbook(
        wb,
        request.budget,
        title,
        overrides_map or None,
        global_bible or None,
    )

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"{title.replace(' ', '_')}_combined.xlsx"
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
