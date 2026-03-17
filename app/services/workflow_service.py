from datetime import datetime, timezone

from app.schemas.ai import (
    CampaignExecutionRequest,
    InventoryOptimizationRequest,
    MenuPricingRequest,
    StaffingOptimizationRequest,
    WorkflowRequest,
    WorkflowResponse,
    WorkflowStep,
)
from app.services.analysis_service import AnalysisService
from app.services.execution_service import ExecutionService
from app.services.operations_service import OperationsService
from app.services.strategy_service import StrategyService


class WorkflowService:
    def __init__(
        self,
        analysis_service: AnalysisService,
        strategy_service: StrategyService,
        execution_service: ExecutionService,
        operations_service: OperationsService,
    ) -> None:
        self.analysis_service = analysis_service
        self.strategy_service = strategy_service
        self.execution_service = execution_service
        self.operations_service = operations_service

    def run(self, payload: WorkflowRequest) -> WorkflowResponse:
        steps: list[WorkflowStep] = []
        outputs: dict[str, str] = {}

        if payload.scenario == "retention_recovery":
            if payload.churn_input is not None:
                churn = self.analysis_service.churn_insight(payload.churn_input)
                steps.append(WorkflowStep(name="analysis", status="completed", detail=churn.summary))
                outputs["analysis"] = churn.summary

            if payload.retention_input is not None:
                strategy = self.strategy_service.retention_offer(payload.retention_input)
                steps.append(WorkflowStep(name="strategy", status="completed", detail=strategy.summary))
                outputs["strategy"] = strategy.summary

                execution = self.execution_service.execute_campaign(
                    CampaignExecutionRequest(
                        campaign_id=f"RET-{payload.store_id}",
                        approved=False,
                        valid_target_count=payload.retention_input.customer_count,
                        channel="coupon",
                        dry_run=payload.dry_run,
                    )
                )
                steps.append(
                    WorkflowStep(name="execution", status=execution.status, detail=execution.message)
                )
                outputs["execution"] = execution.message

        elif payload.scenario == "anomaly_followup":
            if payload.anomaly_input is not None:
                anomaly = self.analysis_service.anomaly_explanation(payload.anomaly_input)
                steps.append(WorkflowStep(name="analysis", status="completed", detail=anomaly.summary))
                outputs["analysis"] = anomaly.summary
            steps.append(
                WorkflowStep(
                    name="strategy",
                    status="skipped",
                    detail="이상 대응 플레이북은 다음 단계 구현 범위입니다.",
                )
            )
            steps.append(
                WorkflowStep(
                    name="execution",
                    status="pending_approval",
                    detail="고위험 이상 대응은 사람 승인 후 실행됩니다.",
                )
            )
            outputs["execution"] = "manual approval required"

        elif payload.scenario == "operations_tuning":
            if payload.menu_input is not None:
                menu_strategy = self.strategy_service.menu_pricing(payload.menu_input)
                steps.append(
                    WorkflowStep(name="strategy", status="completed", detail=menu_strategy.summary)
                )
                outputs["menu_strategy"] = menu_strategy.summary

            if payload.staffing_input is not None:
                staffing = self.operations_service.staffing_optimization(payload.staffing_input)
                steps.append(
                    WorkflowStep(
                        name="staffing",
                        status="completed",
                        detail=staffing.recommendation,
                    )
                )
                outputs["staffing"] = staffing.recommendation

            if payload.inventory_input is not None:
                inventory = self.operations_service.inventory_optimization(payload.inventory_input)
                steps.append(
                    WorkflowStep(
                        name="inventory",
                        status="completed",
                        detail=inventory.recommendation,
                    )
                )
                outputs["inventory"] = inventory.recommendation

        status = "completed"
        if any(step.status == "pending_approval" for step in steps):
            status = "pending_approval"

        workflow_id = datetime.now(timezone.utc).strftime("WF-%Y%m%d-%H%M%S")
        return WorkflowResponse(workflow_id=workflow_id, status=status, steps=steps, outputs=outputs)
