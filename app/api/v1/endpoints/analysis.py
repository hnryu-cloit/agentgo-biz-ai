from fastapi import APIRouter

from app.schemas.ai import (
    AnalysisResponse,
    SalesDiagnosticRequest,
    StoreIntelligenceRequest,
    StoreIntelligenceResponse,
)
from app.services.analysis_service import AnalysisService
from app.services.operations_service import OperationsService
from app.services.store_intelligence_service import StoreIntelligenceService

router = APIRouter()

_analysis_service = AnalysisService()
_operations_service = OperationsService()
_store_intelligence_service = StoreIntelligenceService(_analysis_service, _operations_service)


@router.post("/analysis/sales-diagnostics", response_model=AnalysisResponse)
def sales_diagnostics(payload: SalesDiagnosticRequest) -> AnalysisResponse:
    """매출 추이/요인 분해 진단 API"""
    return _analysis_service.sales_diagnostics(payload)


@router.post("/analysis/store-intelligence", response_model=StoreIntelligenceResponse)
def store_intelligence(payload: StoreIntelligenceRequest) -> StoreIntelligenceResponse:
    """매출·이탈·인력을 통합한 매장 인텔리전스 API"""
    return _store_intelligence_service.analyze(payload)
