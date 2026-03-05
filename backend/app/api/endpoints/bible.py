from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.timing_bible_data import DEFAULT_BIBLE
from app.models.db_models import CustomBibleEntry as DBEntry
from app.models.timing_bible import BibleEntry, TimingBible

router = APIRouter()


# ---------------------------------------------------------------------------
# Official (hardcoded) bible
# ---------------------------------------------------------------------------

@router.get("/bible", response_model=TimingBible)
async def get_bible():
    """Return the built-in Timing Bible."""
    return DEFAULT_BIBLE


@router.get("/bible/lookup/{code}", response_model=BibleEntry | None)
async def lookup_bible_entry(code: str):
    """Look up a single built-in bible entry by account code."""
    return DEFAULT_BIBLE.get_entry(code)


@router.get("/bible/codes", response_model=list[str])
async def get_bible_codes():
    """Return all account codes covered by the built-in bible."""
    return DEFAULT_BIBLE.get_codes()


# ---------------------------------------------------------------------------
# Custom bible (user-defined, stored in the database)
# ---------------------------------------------------------------------------

@router.get("/bible/custom", response_model=list[BibleEntry])
def get_custom_bible(db: Session = Depends(get_db)):
    """Return all user-saved custom bible entries."""
    rows = db.query(DBEntry).order_by(DBEntry.account_code).all()
    return [
        BibleEntry(
            account_code=r.account_code,
            description=r.description,
            timing_pattern=r.timing_pattern,
            timing_title=r.timing_title,
            timing_details=r.timing_details,
            is_custom=True,
        )
        for r in rows
    ]


@router.put("/bible/custom/{code}", response_model=BibleEntry)
def upsert_custom_bible_entry(
    code: str,
    entry: BibleEntry,
    db: Session = Depends(get_db),
):
    """Create or update a custom bible entry for the given account code."""
    if entry.account_code != code:
        raise HTTPException(
            status_code=400,
            detail="account_code in the request body must match the URL code",
        )
    row = db.query(DBEntry).filter(DBEntry.account_code == code).first()
    if row:
        row.description = entry.description
        row.timing_pattern = entry.timing_pattern
        row.timing_title = entry.timing_title
        row.timing_details = entry.timing_details
        row.updated_at = datetime.now(timezone.utc)
    else:
        db.add(
            DBEntry(
                account_code=code,
                description=entry.description,
                timing_pattern=entry.timing_pattern,
                timing_title=entry.timing_title,
                timing_details=entry.timing_details,
            )
        )
    db.commit()
    return BibleEntry(
        account_code=entry.account_code,
        description=entry.description,
        timing_pattern=entry.timing_pattern,
        timing_title=entry.timing_title,
        timing_details=entry.timing_details,
        is_custom=True,
    )


@router.delete("/bible/custom/{code}", status_code=204)
def delete_custom_bible_entry(code: str, db: Session = Depends(get_db)):
    """Remove a custom bible entry."""
    row = db.query(DBEntry).filter(DBEntry.account_code == code).first()
    if row:
        db.delete(row)
        db.commit()
