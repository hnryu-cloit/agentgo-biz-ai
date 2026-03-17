from app.ml.features.inventory import (
    InventoryFeatures,
    inventory_risk_level,
    loss_amount_estimate,
    reorder_quantity,
)
from app.ml.features.staffing import StaffingFeatures, opportunity_cost, staffing_gap, staffing_status
from app.schemas.ai import (
    InventoryOptimizationRequest,
    InventoryOptimizationResponse,
    StaffingOptimizationRequest,
    StaffingOptimizationResponse,
)
from app.services.evidence_service import EvidenceService
from app.services.governance_service import GovernanceService
from app.services.prompt_service import PromptService
from app.services.safety_service import SafetyService


class OperationsService:
    def __init__(self) -> None:
        self.evidence_service = EvidenceService()
        self.governance_service = GovernanceService()
        self.prompt_service = PromptService()
        self.safety_service = SafetyService()

    def staffing_optimization(
        self, payload: StaffingOptimizationRequest
    ) -> StaffingOptimizationResponse:
        features = StaffingFeatures(
            date=str(payload.date),
            store_id=payload.store_id,
            hour=payload.hour,
            sales=payload.sales,
            staff_actual=payload.staff_actual,
            staff_recommended=payload.staff_recommended,
        )
        status = staffing_status(features)
        gap = staffing_gap(features)
        cost = opportunity_cost(features)
        lead = {
            "understaffed": f"{gap}명 추가 투입 또는 피크타임 재배치 권고",
            "overstaffed": f"{abs(gap)}명 재배치 또는 조기 종료 검토",
            "balanced": "현재 인력 배치는 적정 수준입니다.",
        }[status]
        context = (
            f"store_id={payload.store_id}\n"
            f"hour={payload.hour}\n"
            f"sales={payload.sales}\n"
            f"staff_actual={payload.staff_actual}\n"
            f"staff_recommended={payload.staff_recommended}\n"
            f"gap={gap}\n"
            f"opportunity_cost={cost}"
        )
        recommendation = self.prompt_service.render_operations_summary(
            "staffing",
            context=context,
            lead=lead,
        )
        recommendation = self.safety_service.mask_text(recommendation)
        self.safety_service.assert_policy_safe(recommendation)

        evidence = [
            self.evidence_service.build(
                metric="실투입 대비 권장 인력",
                value=f"{payload.staff_actual}명 -> {payload.staff_recommended}명",
                period=f"{payload.date} {payload.hour}:00",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="시간대 매출",
                value=f"{payload.sales:,.0f}원",
                period=f"{payload.date} {payload.hour}:00",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
        ]
        return StaffingOptimizationResponse(
            store_id=payload.store_id,
            status=status,
            gap=gap,
            opportunity_cost=cost,
            recommendation=recommendation,
            evidence=evidence,
            version=self.governance_service.get_version("analysis"),
        )

    def inventory_optimization(
        self, payload: InventoryOptimizationRequest
    ) -> InventoryOptimizationResponse:
        features = InventoryFeatures(
            month=payload.month,
            store_id=payload.store_id,
            item_id=payload.item_id,
            system_qty=payload.system_qty,
            actual_qty=payload.actual_qty,
            loss_rate=payload.loss_rate,
        )
        risk_level = inventory_risk_level(features)
        reorder_qty = reorder_quantity(features)
        estimated_loss = loss_amount_estimate(features)
        lead = {
            "high": "손실 원인 점검 후 즉시 발주 보정과 보관 프로세스 점검이 필요합니다.",
            "medium": "다음 발주에서 안전재고를 반영하고 실사 주기를 단축하세요.",
            "low": "현재 수준 유지, 정기 점검만 권고합니다.",
        }[risk_level]
        context = (
            f"store_id={payload.store_id}\n"
            f"item_id={payload.item_id}\n"
            f"loss_rate={payload.loss_rate:.3f}\n"
            f"system_qty={payload.system_qty}\n"
            f"actual_qty={payload.actual_qty}\n"
            f"reorder_qty={reorder_qty}\n"
            f"estimated_loss_amount={estimated_loss}"
        )
        recommendation = self.prompt_service.render_operations_summary(
            "inventory",
            context=context,
            lead=lead,
        )
        recommendation = self.safety_service.mask_text(recommendation)
        self.safety_service.assert_policy_safe(recommendation)

        evidence = [
            self.evidence_service.build(
                metric="재고 손실율",
                value=f"{payload.loss_rate * 100:.1f}%",
                period=payload.month,
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="시스템 대비 실사 수량",
                value=f"{payload.system_qty:.0f} -> {payload.actual_qty:.0f}",
                period=payload.month,
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
        ]
        return InventoryOptimizationResponse(
            store_id=payload.store_id,
            item_id=payload.item_id,
            risk_level=risk_level,
            reorder_qty=reorder_qty,
            estimated_loss_amount=estimated_loss,
            recommendation=recommendation,
            evidence=evidence,
            version=self.governance_service.get_version("analysis"),
        )
