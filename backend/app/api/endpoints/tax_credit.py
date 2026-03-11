import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.budget import ParsedBudget
from app.models.db_models import TaxCreditOverride
from app.services.tax_credit_writer import BREAKOUT_BIBLE, write_tax_credit_excel

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class BreakoutOverride(BaseModel):
    account_code: str
    description: str = ""
    # None = use default (currency-formula for FOR, bible value for the rest)
    is_foreign: bool | None = None
    is_non_prov: bool | None = None
    fed_labour_pct: float | None = None
    fed_svc_labour_pct: float | None = None
    prov_labour_pct: float | None = None
    prov_svc_labour_pct: float | None = None
    svc_property_pct: float | None = None


class ProjectOverridesResponse(BaseModel):
    project_name: str
    overrides: list[BreakoutOverride]


class SaveOverridesRequest(BaseModel):
    overrides: list[BreakoutOverride]


class TaxCreditRequest(BaseModel):
    budget: ParsedBudget
    title: str = "Untitled"
    overrides: list[BreakoutOverride] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _override_key(project_name: str, account_code: str) -> str:
    return f"{project_name}::{account_code}"


def _bible_defaults(account_code: str, description: str = "") -> BreakoutOverride:
    """Return a BreakoutOverride populated with BREAKOUT_BIBLE defaults for a code."""
    entry = BREAKOUT_BIBLE.get(account_code)
    if entry:
        non_prov_out, pl, fl, psl, sp, fsl = entry
        return BreakoutOverride(
            account_code=account_code,
            description=description,
            is_foreign=None,  # always default to currency-formula
            is_non_prov=non_prov_out,
            fed_labour_pct=fl,
            fed_svc_labour_pct=fsl,
            prov_labour_pct=pl,
            prov_svc_labour_pct=psl,
            svc_property_pct=sp,
        )
    return BreakoutOverride(
        account_code=account_code,
        description=description,
        is_foreign=None,
        is_non_prov=False,
        fed_labour_pct=0.0,
        fed_svc_labour_pct=0.0,
        prov_labour_pct=0.0,
        prov_svc_labour_pct=0.0,
        svc_property_pct=0.0,
    )


def _db_row_to_override(row: TaxCreditOverride, description: str = "") -> BreakoutOverride:
    return BreakoutOverride(
        account_code=row.account_code,
        description=description,
        is_foreign=row.is_foreign,
        is_non_prov=row.is_non_prov,
        fed_labour_pct=row.fed_labour_pct,
        fed_svc_labour_pct=row.fed_svc_labour_pct,
        prov_labour_pct=row.prov_labour_pct,
        prov_svc_labour_pct=row.prov_svc_labour_pct,
        svc_property_pct=row.svc_property_pct,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/tax-credit/overrides/{project_name}", response_model=ProjectOverridesResponse)
async def get_overrides(
    project_name: str,
    account_codes: list[str] = Query(default=[]),
    descriptions: list[str] = Query(default=[]),
    db: Session = Depends(get_db),
):
    """Return breakout overrides for a project, merging bible defaults with any saved values.

    Pass ?account_codes=0201&account_codes=1001&... to specify which codes to include.
    Optionally pass matching ?descriptions=... for display purposes.
    """
    desc_map = dict(zip(account_codes, descriptions)) if descriptions else {}

    # Load any saved overrides for this project
    saved_rows = (
        db.query(TaxCreditOverride)
        .filter(TaxCreditOverride.project_name == project_name)
        .all()
    )
    saved_by_code: dict[str, TaxCreditOverride] = {r.account_code: r for r in saved_rows}

    results: list[BreakoutOverride] = []
    for code in account_codes:
        desc = desc_map.get(code, "")
        if code in saved_by_code:
            ov = _db_row_to_override(saved_by_code[code], desc)
        else:
            ov = _bible_defaults(code, desc)
        results.append(ov)

    return ProjectOverridesResponse(project_name=project_name, overrides=results)


@router.put("/tax-credit/overrides/{project_name}", response_model=ProjectOverridesResponse)
async def save_overrides(
    project_name: str,
    body: SaveOverridesRequest,
    db: Session = Depends(get_db),
):
    """Upsert breakout overrides for a project."""
    for ov in body.overrides:
        key = _override_key(project_name, ov.account_code)
        existing = db.query(TaxCreditOverride).filter(TaxCreditOverride.id == key).first()
        if existing:
            existing.is_foreign = ov.is_foreign
            existing.is_non_prov = ov.is_non_prov
            existing.fed_labour_pct = ov.fed_labour_pct
            existing.fed_svc_labour_pct = ov.fed_svc_labour_pct
            existing.prov_labour_pct = ov.prov_labour_pct
            existing.prov_svc_labour_pct = ov.prov_svc_labour_pct
            existing.svc_property_pct = ov.svc_property_pct
        else:
            db.add(TaxCreditOverride(
                id=key,
                project_name=project_name,
                account_code=ov.account_code,
                is_foreign=ov.is_foreign,
                is_non_prov=ov.is_non_prov,
                fed_labour_pct=ov.fed_labour_pct,
                fed_svc_labour_pct=ov.fed_svc_labour_pct,
                prov_labour_pct=ov.prov_labour_pct,
                prov_svc_labour_pct=ov.prov_svc_labour_pct,
                svc_property_pct=ov.svc_property_pct,
            ))
    db.commit()

    return ProjectOverridesResponse(
        project_name=project_name,
        overrides=body.overrides,
    )


@router.post("/tax-credit/generate")
async def generate_tax_credit_excel(request: TaxCreditRequest):
    overrides_map: dict[str, BreakoutOverride] = {}
    if request.overrides:
        overrides_map = {ov.account_code: ov for ov in request.overrides}

    buffer = write_tax_credit_excel(request.budget, request.title, overrides_map)
    filename = f"{request.title.replace(' ', '_')}_tax_credit_budget.xlsx"

    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
