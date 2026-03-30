from fastapi import APIRouter

from app.api.v1.endpoints import ai, analysis, campaigns, governance, notices, operations, strategy, workflows

api_router = APIRouter()
api_router.include_router(ai.router, prefix="/v1", tags=["ai-legacy"])
api_router.include_router(analysis.router, prefix="/v1", tags=["analysis"])
api_router.include_router(strategy.router, prefix="/v1", tags=["strategy"])
api_router.include_router(operations.router, prefix="/v1", tags=["operations"])
api_router.include_router(campaigns.router, prefix="/v1", tags=["campaigns"])
api_router.include_router(notices.router, prefix="/v1", tags=["notices"])
api_router.include_router(workflows.router, prefix="/v1", tags=["workflows"])
api_router.include_router(governance.router, prefix="/v1", tags=["governance"])
