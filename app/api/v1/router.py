from fastapi import APIRouter

from app.api.v1.endpoints import ai

api_router = APIRouter()
api_router.include_router(ai.router, prefix="/v1", tags=["ai"])
