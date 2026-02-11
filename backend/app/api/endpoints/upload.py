from fastapi import APIRouter, UploadFile, File, HTTPException

from app.models.budget import ParsedBudget
from app.services.excel_parser import parse_budget_excel

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
