from fastapi import APIRouter

from app.schemas.ai import WorkflowRequest, WorkflowResponse
from app.services.analysis_service import AnalysisService
from app.services.execution_service import ExecutionService
from app.services.operations_service import OperationsService
from app.services.strategy_service import StrategyService
from app.services.workflow_service import WorkflowService

router = APIRouter()

_workflow_service = WorkflowService(
    analysis_service=AnalysisService(),
    strategy_service=StrategyService(),
    execution_service=ExecutionService(),
    operations_service=OperationsService(),
)


@router.post("/workflows/run", response_model=WorkflowResponse)
def run_workflow(payload: WorkflowRequest) -> WorkflowResponse:
    """분석→전략→실행 오케스트레이션 워크플로우 API"""
    return _workflow_service.run(payload)