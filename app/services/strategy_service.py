from app.ml.features.menu import MenuFeatures, classify_menu_action, price_adjustment_band, pricing_signal
from app.schemas.ai import (
    CampaignBepSimulationRequest,
    CampaignBepSimulationResponse,
    CampaignUpliftRequest,
    CampaignUpliftResponse,
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

    def campaign_bep_simulation(
        self, payload: CampaignBepSimulationRequest
    ) -> CampaignBepSimulationResponse:
        channel_open_bias = {"sms": 0.78, "push": 0.66, "kakao": 0.72}
        segment_response_bias = {
            "champions": 1.15,
            "loyal": 1.0,
            "at_risk": 0.84,
            "lost": 0.62,
        }
        offer_bias = {
            "discount": 1.0 + min(payload.offer_value / 100, 0.25),
            "coupon": 1.08,
            "free_item": 1.12,
        }

        baseline_open = channel_open_bias[payload.channel]
        demand_signal = min(1.25, max(0.65, 0.85 + payload.return_rate * 1.1))
        roi_signal = min(1.2, max(0.8, 0.92 + (payload.roi_rate / 2000)))
        visit_signal = min(1.15, max(0.85, 0.9 + (payload.recent_visit_count / 4000)))
        fatigue_penalty = 0.94 if payload.target_customers > 2000 else 1.0

        expected_open_rate = min(
            0.92,
            baseline_open
            * segment_response_bias.get(payload.segment_name, 0.9)
            * fatigue_penalty,
        )
        expected_conversion_rate = min(
            0.45,
            max(
                0.03,
                0.08
                * segment_response_bias.get(payload.segment_name, 0.9)
                * offer_bias[payload.offer_type]
                * demand_signal
                * roi_signal
                * visit_signal,
            ),
        )

        expected_incremental_orders = round(payload.target_customers * expected_conversion_rate)
        discount_cost_per_order = (
            payload.menu_price * (payload.offer_value / 100)
            if payload.offer_type == "discount"
            else payload.offer_value
        )
        net_unit_price = max(payload.menu_price - discount_cost_per_order, 0.0)
        unit_profit = max(net_unit_price * payload.margin_rate, 0.0)
        expected_incremental_revenue = expected_incremental_orders * max(payload.avg_order_value, net_unit_price)
        expected_incremental_profit = (expected_incremental_orders * unit_profit) - payload.fixed_cost
        break_even_orders = (
            max(1, round(payload.fixed_cost / unit_profit))
            if unit_profit > 0
            else 999999
        )
        break_even_revenue = break_even_orders * max(payload.avg_order_value, net_unit_price)
        break_even_probability = min(
            0.99,
            max(0.01, expected_incremental_orders / max(break_even_orders, 1)),
        )
        expected_roi = (
            ((expected_incremental_profit) / payload.fixed_cost) * 100
            if payload.fixed_cost > 0
            else 0.0
        )
        confidence = min(
            0.93,
            max(
                0.55,
                0.62
                + min(payload.recent_visit_count, 1000) / 4000
                + min(payload.target_customers, 3000) / 12000,
            ),
        )

        context = (
            f"store_id={payload.store_id}\n"
            f"segment_name={payload.segment_name}\n"
            f"channel={payload.channel}\n"
            f"offer_type={payload.offer_type}\n"
            f"offer_value={payload.offer_value}\n"
            f"target_customers={payload.target_customers}\n"
            f"expected_open_rate={expected_open_rate:.3f}\n"
            f"expected_conversion_rate={expected_conversion_rate:.3f}\n"
            f"break_even_orders={break_even_orders}\n"
            f"expected_incremental_orders={expected_incremental_orders}"
        )
        summary = self.prompt_service.render_strategy_summary(
            "campaign_bep_simulation",
            context=context,
            lead=(
                f"{payload.segment_name} 세그먼트 {payload.target_customers:,}명 대상 "
                f"{payload.channel} 캠페인은 예상 전환율 {expected_conversion_rate * 100:.1f}%로 "
                f"손익분기 {break_even_orders:,}건 대비 {expected_incremental_orders:,}건의 증분 주문이 기대됩니다."
            ),
        )
        summary = self.safety_service.mask_text(summary)
        self.safety_service.assert_policy_safe(summary)

        action_guide = [
            f"{payload.channel} 채널 기준 예상 오픈율은 {expected_open_rate * 100:.1f}%입니다.",
            f"{payload.menu_name} 할인 후 예상 공헌이익 기준 손익분기 주문 수는 {break_even_orders:,}건입니다.",
            f"현재 모델은 BEP 도달 확률을 {break_even_probability * 100:.1f}%로 추정합니다.",
        ]
        if break_even_probability < 0.8:
            action_guide.append("대상 고객 수를 줄이기보다 할인율 조정 또는 loyal 세그먼트 확장이 유리합니다.")
        else:
            action_guide.append("현재 조건으로 발송 후 2일 내 사용률을 점검하면 충분합니다.")

        evidence = [
            self.evidence_service.build(
                metric="예상 오픈율",
                value=f"{expected_open_rate * 100:.1f}%",
                period=f"{payload.promo_days}일 프로모션",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="예상 전환율",
                value=f"{expected_conversion_rate * 100:.1f}%",
                period=f"{payload.promo_days}일 프로모션",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="손익분기 주문 수",
                value=f"{break_even_orders:,}건",
                period=f"{payload.promo_days}일 프로모션",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
        ]

        return CampaignBepSimulationResponse(
            store_id=payload.store_id,
            model_name="campaign-bep-stat-heuristic-0.1.0",
            summary=summary,
            expected_open_rate=round(expected_open_rate, 4),
            expected_conversion_rate=round(expected_conversion_rate, 4),
            expected_incremental_orders=expected_incremental_orders,
            expected_incremental_revenue=round(expected_incremental_revenue, 2),
            expected_incremental_profit=round(expected_incremental_profit, 2),
            break_even_orders=break_even_orders,
            break_even_revenue=round(break_even_revenue, 2),
            break_even_probability=round(break_even_probability, 4),
            expected_roi=round(expected_roi, 2),
            confidence=round(confidence, 4),
            action_guide=action_guide,
            evidence=evidence,
            version=self.governance_service.get_version("strategy"),
        )

    def campaign_uplift_estimate(
        self, payload: CampaignUpliftRequest
    ) -> CampaignUpliftResponse:
        segment_bias = {
            "champions": 0.07,
            "loyal": 0.09,
            "at_risk": 0.11,
            "lost": 0.05,
        }
        channel_bias = {"sms": 1.03, "push": 0.94, "kakao": 1.08}
        discount_bias = min(1.35, 0.95 + payload.discount_rate * 2.4)
        base_redemption = (
            segment_bias.get(payload.segment_name, 0.07)
            * channel_bias[payload.channel]
            * discount_bias
            * max(0.75, min(1.2, 0.85 + payload.return_rate * 1.4))
        )
        expected_redemption_rate = min(0.32, max(0.02, base_redemption))
        expected_incremental_orders = round(payload.target_customers * expected_redemption_rate)
        baseline_orders = max(1, round(payload.recent_visit_count / 7))
        expected_uplift_rate = min(
            1.5,
            max(0.03, expected_incremental_orders / baseline_orders),
        )
        expected_incremental_revenue = round(
            expected_incremental_orders * payload.avg_order_value * max(0.82, 1 - payload.discount_rate * 0.6),
            2,
        )
        confidence = min(
            0.92,
            max(
                0.58,
                0.63 + min(payload.recent_visit_count, 700) / 3500 + min(payload.target_customers, 3000) / 15000,
            ),
        )

        context = (
            f"store_id={payload.store_id}\n"
            f"segment_name={payload.segment_name}\n"
            f"channel={payload.channel}\n"
            f"target_customers={payload.target_customers}\n"
            f"discount_rate={payload.discount_rate:.2f}\n"
            f"expected_redemption_rate={expected_redemption_rate:.3f}\n"
            f"expected_uplift_rate={expected_uplift_rate:.3f}\n"
            f"expected_incremental_orders={expected_incremental_orders}"
        )
        summary = self.prompt_service.render_strategy_summary(
            "campaign_uplift_estimate",
            context=context,
            lead=(
                f"{payload.segment_name} 세그먼트 대상 {payload.channel} 캠페인은 "
                f"미집행 대비 주문 수를 약 {expected_uplift_rate * 100:.1f}% 끌어올리고 "
                f"{expected_incremental_orders:,}건의 추가 주문을 만들 가능성이 있습니다."
            ),
        )
        summary = self.safety_service.mask_text(summary)
        self.safety_service.assert_policy_safe(summary)

        action_guide = [
            f"예상 리딤률은 {expected_redemption_rate * 100:.1f}%입니다.",
            f"추가 주문 {expected_incremental_orders:,}건, 추가 매출 {expected_incremental_revenue:,.0f}원 수준을 기대합니다.",
            "실제 집행 후 48시간 내 오픈율과 사용률로 계수를 재보정하는 편이 맞습니다.",
        ]
        evidence = [
            self.evidence_service.build(
                metric="예상 uplift",
                value=f"{expected_uplift_rate * 100:.1f}%",
                period="캠페인 집행 기간",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="예상 리딤률",
                value=f"{expected_redemption_rate * 100:.1f}%",
                period="캠페인 집행 기간",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
        ]

        return CampaignUpliftResponse(
            store_id=payload.store_id,
            model_name="campaign-uplift-stat-heuristic-0.1.0",
            summary=summary,
            expected_incremental_orders=expected_incremental_orders,
            expected_incremental_revenue=expected_incremental_revenue,
            expected_uplift_rate=round(expected_uplift_rate, 4),
            expected_redemption_rate=round(expected_redemption_rate, 4),
            confidence=round(confidence, 4),
            action_guide=action_guide,
            evidence=evidence,
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
