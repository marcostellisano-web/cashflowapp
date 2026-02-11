from fastapi import APIRouter, Query

from app.models.distribution import LineItemDistribution
from app.services.phase_mapper import get_default_distributions

router = APIRouter()


@router.get("/defaults/distributions", response_model=list[LineItemDistribution])
async def get_defaults(codes: list[str] = Query(...)):
    return get_default_distributions(codes)
