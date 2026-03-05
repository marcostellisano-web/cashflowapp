from fastapi import APIRouter

from app.api.endpoints import upload, cashflow, defaults, bible, tax_credit

api_router = APIRouter()
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(cashflow.router, tags=["cashflow"])
api_router.include_router(defaults.router, tags=["defaults"])
api_router.include_router(bible.router, tags=["bible"])
api_router.include_router(tax_credit.router, tags=["tax-credit"])
