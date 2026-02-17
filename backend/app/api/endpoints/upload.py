from io import BytesIO

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from app.models.budget import ParsedBudget
from app.models.production import ProductionParameters
from app.services.excel_parser import parse_budget_excel
from app.services.parameters_parser import generate_parameters_template, parse_parameters_excel

router = APIRouter()


@router.post("/upload", response_model=ParsedBudget)
async def upload_budget(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")

    try:
        parsed = parse_budget_excel(file.file, filename=file.filename or "uploaded.xlsx")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse budget file: {e}")

    return parsed


@router.post("/upload/parameters", response_model=ProductionParameters)
async def upload_parameters(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")

    try:
        params = parse_parameters_excel(file.file)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse parameters file: {e}")

    return params


@router.get("/upload/parameters/template")
async def download_parameters_template():
    buf = generate_parameters_template()
    return StreamingResponse(
        BytesIO(buf.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="parameters_template.xlsx"'},
    )
