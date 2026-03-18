from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

from app.schemas.ai import (
    AnomalyExplanationRequest,
    AnalysisResponse,
    CampaignExecutionRequest,
    CampaignExecutionResponse,
    CampaignBepSimulationRequest,
    CampaignBepSimulationResponse,
    CampaignUpliftRequest,
    CampaignUpliftResponse,
    CampaignTargetValidationRequest,
    CampaignTargetValidationResponse,
    ChurnInsightRequest,
    GovernanceRegistryResponse,
    InventoryOptimizationRequest,
    InventoryOptimizationResponse,
    MenuPricingRequest,
    MenuPricingResponse,
    OCRResponse,
    RetentionOfferRequest,
    SalesDiagnosticRequest,
    StaffingOptimizationRequest,
    StaffingOptimizationResponse,
    StoreIntelligenceRequest,
    StoreIntelligenceResponse,
    StrategyResponse,
    WorkflowRequest,
    WorkflowResponse,
)
from app.services.analysis_service import AnalysisService
from app.services.execution_service import ExecutionService
from app.services.governance_service import GovernanceService
from app.services.ocr_service import OCRService
from app.services.operations_service import OperationsService
from app.services.strategy_service import StrategyService
from app.services.store_intelligence_service import StoreIntelligenceService
from app.services.workflow_service import WorkflowService

router = APIRouter()

analysis_service = AnalysisService()
strategy_service = StrategyService()
execution_service = ExecutionService()
ocr_service = OCRService()
governance_service = GovernanceService()
operations_service = OperationsService()
workflow_service = WorkflowService(
    analysis_service=analysis_service,
    strategy_service=strategy_service,
    execution_service=execution_service,
    operations_service=operations_service,
)
store_intelligence_service = StoreIntelligenceService(
    analysis_service=analysis_service,
    operations_service=operations_service,
)


@router.get("/governance/registry", response_model=GovernanceRegistryResponse)
async def get_registry() -> GovernanceRegistryResponse:
    return governance_service.get_registry()


@router.post("/analysis/sales-diagnostics", response_model=AnalysisResponse)
async def sales_diagnostics(payload: SalesDiagnosticRequest) -> AnalysisResponse:
    return analysis_service.sales_diagnostics(payload)


@router.post("/analysis/churn-insights", response_model=AnalysisResponse)
async def churn_insights(payload: ChurnInsightRequest) -> AnalysisResponse:
    return analysis_service.churn_insight(payload)


@router.post("/analysis/anomalies/explain", response_model=AnalysisResponse)
async def anomaly_explain(payload: AnomalyExplanationRequest) -> AnalysisResponse:
    return analysis_service.anomaly_explanation(payload)


@router.post("/analysis/store-intelligence", response_model=StoreIntelligenceResponse)
async def store_intelligence(payload: StoreIntelligenceRequest) -> StoreIntelligenceResponse:
    return store_intelligence_service.analyze(payload)


@router.post("/strategy/retention-offer", response_model=StrategyResponse)
async def retention_offer(payload: RetentionOfferRequest) -> StrategyResponse:
    return strategy_service.retention_offer(payload)


@router.post("/strategy/menu-pricing", response_model=MenuPricingResponse)
async def menu_pricing(payload: MenuPricingRequest) -> MenuPricingResponse:
    return strategy_service.menu_pricing(payload)


@router.post("/campaigns/validate-targets", response_model=CampaignTargetValidationResponse)
async def validate_targets(
    payload: CampaignTargetValidationRequest,
) -> CampaignTargetValidationResponse:
    return execution_service.validate_targets(payload)


@router.post("/campaigns/execute", response_model=CampaignExecutionResponse)
async def execute_campaign(
    payload: CampaignExecutionRequest,
) -> CampaignExecutionResponse:
    return execution_service.execute_campaign(payload)


@router.post("/campaigns/simulate-bep", response_model=CampaignBepSimulationResponse)
async def simulate_campaign_bep(
    payload: CampaignBepSimulationRequest,
) -> CampaignBepSimulationResponse:
    return strategy_service.campaign_bep_simulation(payload)


@router.post("/campaigns/predict-uplift", response_model=CampaignUpliftResponse)
async def predict_campaign_uplift(
    payload: CampaignUpliftRequest,
) -> CampaignUpliftResponse:
    return strategy_service.campaign_uplift_estimate(payload)


@router.post("/operations/staffing", response_model=StaffingOptimizationResponse)
async def staffing_optimization(
    payload: StaffingOptimizationRequest,
) -> StaffingOptimizationResponse:
    return operations_service.staffing_optimization(payload)


@router.post("/operations/inventory", response_model=InventoryOptimizationResponse)
async def inventory_optimization(
    payload: InventoryOptimizationRequest,
) -> InventoryOptimizationResponse:
    return operations_service.inventory_optimization(payload)


@router.post("/workflows/run", response_model=WorkflowResponse)
async def run_workflow(payload: WorkflowRequest) -> WorkflowResponse:
    return workflow_service.run(payload)


@router.post("/notices/ocr", response_model=OCRResponse)
async def notice_ocr(
    file: Optional[UploadFile] = File(default=None),
    raw_text: Optional[str] = Form(default=None),
    source_name: str = Form(default="notice.txt"),
    uploaded_at: str = Form(default="2026-03-15T09:00:00+09:00"),
) -> OCRResponse:
    return await ocr_service.parse_notice(
        upload=file,
        raw_text=raw_text,
        source_name=source_name,
        uploaded_at=uploaded_at,
    )
