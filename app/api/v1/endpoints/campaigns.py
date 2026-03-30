from fastapi import APIRouter

from app.schemas.ai import (
    CampaignExecutionRequest,
    CampaignExecutionResponse,
    CampaignTargetValidationRequest,
    CampaignTargetValidationResponse,
)
from app.services.execution_service import ExecutionService

router = APIRouter()

_execution_service = ExecutionService()


@router.post("/campaigns/validate-targets", response_model=CampaignTargetValidationResponse)
def validate_targets(payload: CampaignTargetValidationRequest) -> CampaignTargetValidationResponse:
    """캠페인 대상 고객 검증 및 위반 대상 제외 API"""
    return _execution_service.validate_targets(payload)


@router.post("/campaigns/execute", response_model=CampaignExecutionResponse)
def execute_campaign(payload: CampaignExecutionRequest) -> CampaignExecutionResponse:
    """캠페인 실행 handoff API"""
    return _execution_service.execute_campaign(payload)