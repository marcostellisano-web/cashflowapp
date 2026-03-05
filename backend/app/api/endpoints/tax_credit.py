from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

from app.models.budget import ParsedBudget
from app.services.tax_credit_writer import write_tax_credit_excel

router = APIRouter()


class TaxCreditRequest(BaseModel):
    budget: ParsedBudget
    title: str = "Untitled"


@router.post("/tax-credit/generate")
async def generate_tax_credit_excel(request: TaxCreditRequest):
    buffer = write_tax_credit_excel(request.budget, request.title)
    filename = f"{request.title.replace(' ', '_')}_tax_credit_budget.xlsx"

    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
