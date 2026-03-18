from app.schemas.ai import (
    StoreIntelligenceRequest,
    StoreIntelligenceResponse,
)
from app.services.analysis_service import AnalysisService
from app.services.governance_service import GovernanceService
from app.services.operations_service import OperationsService
from app.services.safety_service import SafetyService


class StoreIntelligenceService:
    def __init__(
        self,
        analysis_service: AnalysisService,
        operations_service: OperationsService,
    ) -> None:
        self.analysis_service = analysis_service
        self.operations_service = operations_service
        self.governance_service = GovernanceService()
        self.safety_service = SafetyService()

    def analyze(self, payload: StoreIntelligenceRequest) -> StoreIntelligenceResponse:
        sales = self.analysis_service.sales_diagnostics(payload.sales_input)
        churn = self.analysis_service.churn_insight(payload.churn_input)
        staffing = [
            self.operations_service.staffing_optimization(item)
            for item in payload.staffing_inputs
        ]

        primary_staffing = staffing[0] if staffing else None
        staffing_summary = (
            primary_staffing.recommendation if primary_staffing else "시간대별 인력 데이터가 부족해 운영 권고를 생략합니다."
        )
        summary = (
            f"{sales.summary} "
            f"{churn.summary} "
            f"프로모션 ROI는 {payload.roi_rate:.1f}%이고 평균 객단가는 {payload.avg_order_value:,.0f}원입니다. "
            f"{staffing_summary}"
        )
        summary = self.safety_service.mask_text(summary)
        self.safety_service.assert_policy_safe(summary)

        priority_actions: list[str] = []
        priority_actions.extend(sales.highlights[:2])
        priority_actions.extend(churn.highlights[:2])
        if primary_staffing:
            priority_actions.append(primary_staffing.recommendation)
        priority_actions.append(
            f"최근 방문 {payload.recent_visit_count:,}건 기준으로 재방문 고객 액션 우선순위를 점검하세요."
        )

        return StoreIntelligenceResponse(
            store_id=payload.store_id,
            summary=summary,
            priority_actions=priority_actions[:5],
            sales=sales,
            churn=churn,
            staffing=staffing,
            version=self.governance_service.get_version("analysis"),
        )
