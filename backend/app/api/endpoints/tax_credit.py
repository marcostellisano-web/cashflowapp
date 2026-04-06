from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.budget import ParsedBudget
from app.models.db_models import BiblePreset, BiblePresetEntry, BreakoutBibleEntry, TaxCreditOverride
from app.services.bible_parser import parse_bible_excel
from app.services.tax_credit_writer import (
    BREAKOUT_BIBLE,
    write_bible_excel,
    write_tax_credit_excel,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class BreakoutOverride(BaseModel):
    account_code: str
    description: str = ""
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


class BibleEntrySchema(BaseModel):
    account_code: str
    description: str = ""
    is_non_prov: bool
    prov_labour_pct: float
    fed_labour_pct: float
    prov_svc_labour_pct: float
    svc_property_pct: float
    fed_svc_labour_pct: float
    is_customized: bool = False   # True when a manual breakout_bible_entries row exists
    is_standard: bool = True      # False when account_code is not in BREAKOUT_BIBLE
    is_from_preset: bool = False  # True when value comes from the active preset


class TaxCreditRequest(BaseModel):
    budget: ParsedBudget
    title: str = "Untitled"
    overrides: list[BreakoutOverride] | None = None


class BiblePresetSchema(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime
    entry_count: int


class BiblePresetUploadResponse(BaseModel):
    preset_id: int
    name: str
    entry_count: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _override_key(project_name: str, account_code: str) -> str:
    return f"{project_name}::{account_code}"


def _bible_defaults(account_code: str, description: str = "") -> BreakoutOverride:
    entry = BREAKOUT_BIBLE.get(account_code)
    if entry:
        non_prov_out, pl, fl, psl, sp, fsl = entry
        return BreakoutOverride(
            account_code=account_code,
            description=description,
            is_foreign=None,
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


def _load_global_bible(db: Session) -> dict:
    """Return effective bible overrides as a tuple-dict for write_tax_credit_excel.

    Resolution order (later entries win):
      1. Active preset entries  (if any preset is marked is_active)
      2. Manual breakout_bible_entries overrides
    """
    result: dict = {}

    active_preset = db.query(BiblePreset).filter(BiblePreset.is_active == True).first()
    if active_preset:
        for e in db.query(BiblePresetEntry).filter(
            BiblePresetEntry.preset_id == active_preset.id
        ).all():
            result[e.account_code] = (
                e.is_non_prov,
                e.prov_labour_pct,
                e.fed_labour_pct,
                e.prov_svc_labour_pct,
                e.svc_property_pct,
                e.fed_svc_labour_pct,
            )

    for r in db.query(BreakoutBibleEntry).all():
        result[r.account_code] = (
            r.is_non_prov,
            r.prov_labour_pct,
            r.fed_labour_pct,
            r.prov_svc_labour_pct,
            r.svc_property_pct,
            r.fed_svc_labour_pct,
        )

    return result


def _get_active_preset_dict(db: Session) -> dict:
    """Return active preset entries keyed by account_code (raw row objects)."""
    preset = db.query(BiblePreset).filter(BiblePreset.is_active == True).first()
    if not preset:
        return {}
    return {
        e.account_code: e
        for e in db.query(BiblePresetEntry).filter(
            BiblePresetEntry.preset_id == preset.id
        ).all()
    }


# ---------------------------------------------------------------------------
# Bible endpoints
# ---------------------------------------------------------------------------

@router.get("/tax-credit/bible/excel")
async def download_bible_excel(db: Session = Depends(get_db)):
    """Download the full effective breakout bible as a formatted Excel file."""
    db_rows = {r.account_code: r for r in db.query(BreakoutBibleEntry).all()}

    entries = []
    for code, defaults in BREAKOUT_BIBLE.items():
        non_prov, pl, fl, psl, sp, fsl = defaults
        if code in db_rows:
            r = db_rows[code]
            entries.append({
                "account_code": code,
                "is_non_prov": r.is_non_prov,
                "prov_labour_pct": r.prov_labour_pct,
                "fed_labour_pct": r.fed_labour_pct,
                "prov_svc_labour_pct": r.prov_svc_labour_pct,
                "svc_property_pct": r.svc_property_pct,
                "fed_svc_labour_pct": r.fed_svc_labour_pct,
                "is_customized": True,
            })
        else:
            entries.append({
                "account_code": code,
                "is_non_prov": non_prov,
                "prov_labour_pct": pl,
                "fed_labour_pct": fl,
                "prov_svc_labour_pct": psl,
                "svc_property_pct": sp,
                "fed_svc_labour_pct": fsl,
                "is_customized": False,
            })

    buffer = write_bible_excel(entries)
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="breakout_bible.xlsx"'},
    )


# ---------------------------------------------------------------------------
# Project overrides endpoints
# ---------------------------------------------------------------------------

@router.get("/tax-credit/overrides/{project_name}", response_model=ProjectOverridesResponse)
async def get_overrides(
    project_name: str,
    account_codes: list[str] = Query(default=[]),
    descriptions: list[str] = Query(default=[]),
    db: Session = Depends(get_db),
):
    desc_map = dict(zip(account_codes, descriptions)) if descriptions else {}

    saved_rows = (
        db.query(TaxCreditOverride)
        .filter(TaxCreditOverride.project_name == project_name)
        .all()
    )
    saved_by_code = {r.account_code: r for r in saved_rows}

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
    for ov in body.overrides:
        key = _override_key(project_name, ov.account_code)
        existing = db.query(TaxCreditOverride).filter(TaxCreditOverride.id == key).first()
        if existing:
            existing.is_foreign          = ov.is_foreign
            existing.is_non_prov         = ov.is_non_prov
            existing.fed_labour_pct      = ov.fed_labour_pct
            existing.fed_svc_labour_pct  = ov.fed_svc_labour_pct
            existing.prov_labour_pct     = ov.prov_labour_pct
            existing.prov_svc_labour_pct = ov.prov_svc_labour_pct
            existing.svc_property_pct    = ov.svc_property_pct
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
    return ProjectOverridesResponse(project_name=project_name, overrides=body.overrides)


@router.get("/tax-credit/bible", response_model=list[BibleEntrySchema])
async def get_bible(db: Session = Depends(get_db)):
    """Return the effective breakout bible for the editor.

    Merges (in ascending priority):
      1. BREAKOUT_BIBLE hardcoded defaults
      2. Active preset entries (if any)
      3. Manual breakout_bible_entries overrides
    """
    db_rows: dict[str, BreakoutBibleEntry] = {
        r.account_code: r
        for r in db.query(BreakoutBibleEntry).all()
    }
    preset_rows = _get_active_preset_dict(db)

    # Collect all known account codes across all sources
    all_codes = set(BREAKOUT_BIBLE) | set(preset_rows) | set(db_rows)

    results: list[BibleEntrySchema] = []
    for code in all_codes:
        is_standard = code in BREAKOUT_BIBLE
        manual_row = db_rows.get(code)
        preset_row = preset_rows.get(code)

        if manual_row:
            # Manual override wins — show its values
            results.append(BibleEntrySchema(
                account_code=code,
                description=manual_row.description,
                is_non_prov=manual_row.is_non_prov,
                prov_labour_pct=manual_row.prov_labour_pct,
                fed_labour_pct=manual_row.fed_labour_pct,
                prov_svc_labour_pct=manual_row.prov_svc_labour_pct,
                svc_property_pct=manual_row.svc_property_pct,
                fed_svc_labour_pct=manual_row.fed_svc_labour_pct,
                is_customized=True,
                is_standard=is_standard,
                is_from_preset=False,
            ))
        elif preset_row:
            # Preset value (no manual override)
            results.append(BibleEntrySchema(
                account_code=code,
                description=preset_row.description,
                is_non_prov=preset_row.is_non_prov,
                prov_labour_pct=preset_row.prov_labour_pct,
                fed_labour_pct=preset_row.fed_labour_pct,
                prov_svc_labour_pct=preset_row.prov_svc_labour_pct,
                svc_property_pct=preset_row.svc_property_pct,
                fed_svc_labour_pct=preset_row.fed_svc_labour_pct,
                is_customized=False,
                is_standard=is_standard,
                is_from_preset=True,
            ))
        else:
            # Hardcoded default
            non_prov, pl, fl, psl, sp, fsl = BREAKOUT_BIBLE[code]
            results.append(BibleEntrySchema(
                account_code=code,
                description="",
                is_non_prov=non_prov,
                prov_labour_pct=pl,
                fed_labour_pct=fl,
                prov_svc_labour_pct=psl,
                svc_property_pct=sp,
                fed_svc_labour_pct=fsl,
                is_customized=False,
                is_standard=True,
                is_from_preset=False,
            ))

    results.sort(key=lambda e: e.account_code)
    return results


@router.put("/tax-credit/bible/{account_code}", response_model=BibleEntrySchema)
async def upsert_bible_entry(
    account_code: str,
    body: BibleEntrySchema,
    db: Session = Depends(get_db),
):
    """Create or update a breakout bible entry in the database."""
    row = db.query(BreakoutBibleEntry).filter(
        BreakoutBibleEntry.account_code == account_code
    ).first()
    if row:
        row.description         = body.description
        row.is_non_prov         = body.is_non_prov
        row.prov_labour_pct     = body.prov_labour_pct
        row.fed_labour_pct      = body.fed_labour_pct
        row.prov_svc_labour_pct = body.prov_svc_labour_pct
        row.svc_property_pct    = body.svc_property_pct
        row.fed_svc_labour_pct  = body.fed_svc_labour_pct
    else:
        db.add(BreakoutBibleEntry(
            account_code        = account_code,
            description         = body.description,
            is_non_prov         = body.is_non_prov,
            prov_labour_pct     = body.prov_labour_pct,
            fed_labour_pct      = body.fed_labour_pct,
            prov_svc_labour_pct = body.prov_svc_labour_pct,
            svc_property_pct    = body.svc_property_pct,
            fed_svc_labour_pct  = body.fed_svc_labour_pct,
        ))
    db.commit()
    is_standard = account_code in BREAKOUT_BIBLE
    return BibleEntrySchema(**body.model_dump(), is_customized=True, is_standard=is_standard)


@router.delete("/tax-credit/bible/{account_code}", status_code=204)
async def delete_bible_entry(account_code: str, db: Session = Depends(get_db)):
    """Delete the DB override for a bible entry (reverts standard entries to defaults,
    fully removes custom entries)."""
    row = db.query(BreakoutBibleEntry).filter(
        BreakoutBibleEntry.account_code == account_code
    ).first()
    if row:
        db.delete(row)
        db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Bible preset endpoints
# ---------------------------------------------------------------------------

@router.get("/tax-credit/bible/presets", response_model=list[BiblePresetSchema])
async def list_bible_presets(db: Session = Depends(get_db)):
    """Return all saved bible presets."""
    presets = db.query(BiblePreset).order_by(BiblePreset.created_at.desc()).all()
    results = []
    for p in presets:
        count = db.query(BiblePresetEntry).filter(BiblePresetEntry.preset_id == p.id).count()
        results.append(BiblePresetSchema(
            id=p.id,
            name=p.name,
            is_active=p.is_active,
            created_at=p.created_at,
            entry_count=count,
        ))
    return results


@router.post("/tax-credit/bible/presets/upload", response_model=BiblePresetUploadResponse)
async def upload_bible_preset(
    file: UploadFile = File(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    """Upload an Excel file as a new named bible preset."""
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")

    try:
        entries = parse_bible_excel(file.file)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse bible file: {e}")

    preset = BiblePreset(name=name.strip() or "Untitled", is_active=False)
    db.add(preset)
    db.flush()  # get preset.id before inserting entries

    for entry in entries:
        db.add(BiblePresetEntry(
            preset_id           = preset.id,
            account_code        = entry["account_code"],
            description         = entry["description"],
            is_non_prov         = entry["is_non_prov"],
            prov_labour_pct     = entry["prov_labour_pct"],
            fed_labour_pct      = entry["fed_labour_pct"],
            prov_svc_labour_pct = entry["prov_svc_labour_pct"],
            svc_property_pct    = entry["svc_property_pct"],
            fed_svc_labour_pct  = entry["fed_svc_labour_pct"],
        ))

    db.commit()
    return BiblePresetUploadResponse(
        preset_id=preset.id,
        name=preset.name,
        entry_count=len(entries),
    )


@router.put("/tax-credit/bible/presets/{preset_id}/activate", response_model=BiblePresetSchema)
async def activate_bible_preset(preset_id: int, db: Session = Depends(get_db)):
    """Set a preset as active (deactivates all others)."""
    target = db.query(BiblePreset).filter(BiblePreset.id == preset_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Preset not found")

    db.query(BiblePreset).update({BiblePreset.is_active: False})
    target.is_active = True
    db.commit()

    count = db.query(BiblePresetEntry).filter(BiblePresetEntry.preset_id == target.id).count()
    return BiblePresetSchema(
        id=target.id,
        name=target.name,
        is_active=True,
        created_at=target.created_at,
        entry_count=count,
    )


@router.delete("/tax-credit/bible/presets/{preset_id}/deactivate", response_model=BiblePresetSchema)
async def deactivate_bible_preset(preset_id: int, db: Session = Depends(get_db)):
    """Deactivate a preset (falls back to hardcoded defaults)."""
    target = db.query(BiblePreset).filter(BiblePreset.id == preset_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Preset not found")

    target.is_active = False
    db.commit()

    count = db.query(BiblePresetEntry).filter(BiblePresetEntry.preset_id == target.id).count()
    return BiblePresetSchema(
        id=target.id,
        name=target.name,
        is_active=False,
        created_at=target.created_at,
        entry_count=count,
    )


@router.delete("/tax-credit/bible/presets/{preset_id}", status_code=204)
async def delete_bible_preset(preset_id: int, db: Session = Depends(get_db)):
    """Delete a preset and all its entries."""
    preset = db.query(BiblePreset).filter(BiblePreset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    db.query(BiblePresetEntry).filter(BiblePresetEntry.preset_id == preset_id).delete()
    db.delete(preset)
    db.commit()
    return Response(status_code=204)


@router.post("/tax-credit/generate")
async def generate_tax_credit_excel(
    request: TaxCreditRequest,
    db: Session = Depends(get_db),
):
    overrides_map: dict[str, BreakoutOverride] = {}
    if request.overrides:
        overrides_map = {ov.account_code: ov for ov in request.overrides}

    global_bible = _load_global_bible(db)

    buffer = write_tax_credit_excel(
        request.budget,
        request.title,
        overrides_map,
        global_bible or None,
    )
    filename = f"{request.title.replace(' ', '_')}_tax_credit_budget.xlsx"

    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
