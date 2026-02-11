from io import BytesIO

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.budget import ParsedBudget
from app.models.cashflow import CashflowOutput, GenerateRequest
from app.services.cashflow_engine import generate_cashflow
from app.services.excel_writer import write_cashflow_excel

router = APIRouter()


@router.post("/cashflow/preview", response_model=CashflowOutput)
async def preview_cashflow(request: GenerateRequest):
    output = generate_cashflow(
        budget=request.budget,
        parameters=request.parameters,
        distributions=request.distributions,
    )
    return output


@router.post("/cashflow/generate")
async def generate_cashflow_excel(request: GenerateRequest):
    output = generate_cashflow(
        budget=request.budget,
        parameters=request.parameters,
        distributions=request.distributions,
    )
    buffer = write_cashflow_excel(output, request.parameters)
    filename = f"{request.parameters.title.replace(' ', '_')}_cashflow.xlsx"

    return StreamingResponse(
        BytesIO(buffer.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
