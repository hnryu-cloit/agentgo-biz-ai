from app.ml.features.menu import MenuFeatures, classify_menu_action, price_adjustment_band, pricing_signal
from app.schemas.ai import (
    MenuPricingRequest,
    MenuPricingResponse,
    RetentionOfferRequest,
    StrategyAction,
    StrategyResponse,
    WarningMessage,
)
from app.services.evidence_service import EvidenceService
from app.services.governance_service import GovernanceService
from app.services.prompt_service import PromptService
from app.services.safety_service import SafetyService
from app.services.sufficiency_service import SufficiencyService


class StrategyService:
    def __init__(self) -> None:
        self.evidence_service = EvidenceService()
        self.governance_service = GovernanceService()
        self.prompt_service = PromptService()
        self.safety_service = SafetyService()
        self.sufficiency_service = SufficiencyService()

    def retention_offer(self, payload: RetentionOfferRequest) -> StrategyResponse:
        warnings = self.sufficiency_service.validate_retention_input(payload)
        discount = 3000 if payload.churn_risk_level == "high" else 2000 if payload.churn_risk_level == "medium" else 1000
        if payload.coupon_budget and payload.customer_count > 0:
            discount = min(discount, max(payload.coupon_budget // payload.customer_count, 500))

        expected_return = 0.18 if payload.churn_risk_level == "high" else 0.11 if payload.churn_risk_level == "medium" else 0.06
        context = (
            f"store_id={payload.store_id}\n"
            f"segment_name={payload.segment_name}\n"
            f"customer_count={payload.customer_count}\n"
            f"churn_risk_level={payload.churn_risk_level}\n"
            f"coupon_budget={payload.coupon_budget}\n"
            f"recommended_discount={discount}"
        )
        summary = self.prompt_service.render_strategy_summary(
            "retention_offer",
            context=context,
            lead=(
                f"{payload.segment_name} 세그먼트 {payload.customer_count}명에게 "
                f"{discount:,}원 수준 복귀 오퍼를 제안합니다."
            ),
        )
        summary = self.safety_service.mask_text(summary)
        self.safety_service.assert_policy_safe(summary)

        actions = [
            StrategyAction(
                title=f"{payload.segment_name} 타깃 쿠폰 발송",
                expected_effect=f"예상 복귀율 {expected_return * 100:.1f}%, 예상 매출 {payload.avg_margin_per_customer * payload.customer_count * expected_return:,.0f}원",
                priority="P0",
            ),
            StrategyAction(
                title="7일 쿨다운 적용",
                expected_effect="과발송 방지 및 동의 정책 위반 위험 감소",
                priority="P0",
            ),
            StrategyAction(
                title="미반응 고객 리마인드 메시지",
                expected_effect="쿠폰 미사용 고객의 2차 반응률 개선",
                priority="P1",
            ),
        ]

        evidence = [
            self.evidence_service.build(
                metric="세그먼트 규모",
                value=str(payload.customer_count),
                period="최근 캠페인 기준",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="고객당 평균 기여마진",
                value=f"{payload.avg_margin_per_customer:,.0f}원",
                period="최근 30일",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
        ]
        return StrategyResponse(
            store_id=payload.store_id,
            strategy_type="retention_offer",
            summary=summary,
            actions=actions,
            evidence=evidence,
            warnings=warnings,
            version=self.governance_service.get_version("strategy"),
        )

    def menu_pricing(self, payload: MenuPricingRequest) -> MenuPricingResponse:
        features = MenuFeatures(
            menu_id=payload.menu_id,
            store_id=payload.store_id,
            price=payload.price,
            cost=payload.cost,
            quantity=payload.quantity,
            margin_rate=payload.margin_rate,
            category=payload.category,
        )
        signal = pricing_signal(features)
        action = classify_menu_action(features, signal)
        recommended_price_min, recommended_price_max = price_adjustment_band(features)

        context = (
            f"store_id={payload.store_id}\n"
            f"menu_id={payload.menu_id}\n"
            f"price={payload.price}\n"
            f"cost={payload.cost}\n"
            f"quantity={payload.quantity}\n"
            f"margin_rate={payload.margin_rate:.3f}\n"
            f"pricing_signal={signal}\n"
            f"action={action}\n"
            f"recommended_price_range={recommended_price_min}-{recommended_price_max}"
        )
        summary = self.prompt_service.render_strategy_summary(
            "menu_pricing",
            context=context,
            lead=(
                f"메뉴 {payload.menu_id}는 현재 마진율 {payload.margin_rate * 100:.1f}% 기준으로 "
                f"`{action}` 전략이 적합하며 권장 가격 범위는 {recommended_price_min:,}원~{recommended_price_max:,}원입니다."
            ),
        )
        summary = self.safety_service.mask_text(summary)
        self.safety_service.assert_policy_safe(summary)

        action_descriptions = {
            "price_up_test": "소폭 가격 인상 A/B 테스트",
            "bundle_promotion": "번들 또는 세트 프로모션 우선",
            "cost_review": "원가 재점검 후 메뉴 구조 조정",
            "maintain": "현재 가격 유지",
        }
        actions = [
            StrategyAction(
                title=action_descriptions[action],
                expected_effect=f"권장 가격 범위 {recommended_price_min:,}원~{recommended_price_max:,}원 내에서 마진 방어",
                priority="P0",
            ),
            StrategyAction(
                title="실행 전 2주 매출 추이 비교",
                expected_effect="급격한 가격 변경에 따른 수요 하락 리스크 통제",
                priority="P1",
            ),
        ]

        evidence = [
            self.evidence_service.build(
                metric="현재 가격/원가",
                value=f"{payload.price:,}원 / {payload.cost:,.0f}원",
                period="최근 집계 기준",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="판매량 및 마진율",
                value=f"{payload.quantity:.0f}개 / {payload.margin_rate * 100:.1f}%",
                period="최근 집계 기준",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
        ]

        warnings: list[WarningMessage] = []
        if payload.margin_rate < 0.2:
            warnings.append(
                WarningMessage(
                    code="low_margin_emergency",
                    message="마진율이 매우 낮아 즉시 원가 점검이 필요합니다.",
                )
            )

        return MenuPricingResponse(
            store_id=payload.store_id,
            menu_id=payload.menu_id,
            strategy_type="menu_pricing",
            action=action,
            pricing_signal=signal,
            recommended_price_min=recommended_price_min,
            recommended_price_max=recommended_price_max,
            summary=summary,
            actions=actions,
            evidence=evidence,
            warnings=warnings,
            version=self.governance_service.get_version("strategy"),
        )
