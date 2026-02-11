from fastapi import APIRouter

from app.api.endpoints import upload, cashflow, defaults

api_router = APIRouter()
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(cashflow.router, tags=["cashflow"])
api_router.include_router(defaults.router, tags=["defaults"])
