from fastapi import APIRouter

from app.domain.timing_bible_data import DEFAULT_BIBLE
from app.models.timing_bible import BibleEntry, TimingBible

router = APIRouter()


@router.get("/bible", response_model=TimingBible)
async def get_bible():
    """Return the current Timing Bible."""
    return DEFAULT_BIBLE


@router.get("/bible/lookup/{code}", response_model=BibleEntry | None)
async def lookup_bible_entry(code: str):
    """Look up a single bible entry by account code."""
    return DEFAULT_BIBLE.get_entry(code)


@router.get("/bible/codes", response_model=list[str])
async def get_bible_codes():
    """Return all account codes covered by the bible."""
    return DEFAULT_BIBLE.get_codes()
