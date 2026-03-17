from app.ml.features.anomaly import classify_anomaly
from app.ml.features.churn import ChurnFeatures, build_churn_score, classify_churn_risk
from app.ml.features.sales import factor_scores_from_deltas
from app.schemas.ai import (
    AnalysisResponse,
    AnomalyExplanationRequest,
    ChurnInsightRequest,
    SalesDiagnosticRequest,
)
from app.services.evidence_service import EvidenceService
from app.services.governance_service import GovernanceService
from app.services.prompt_service import PromptService
from app.services.safety_service import SafetyService
from app.services.sufficiency_service import SufficiencyService


class AnalysisService:
    def __init__(self) -> None:
        self.evidence_service = EvidenceService()
        self.governance_service = GovernanceService()
        self.prompt_service = PromptService()
        self.safety_service = SafetyService()
        self.sufficiency_service = SufficiencyService()

    def sales_diagnostics(self, payload: SalesDiagnosticRequest) -> AnalysisResponse:
        warnings, cold_start = self.sufficiency_service.validate_analysis_input(payload)
        labels = {
            "customer_count": "객수 감소",
            "avg_ticket": "객단가 변동",
            "channel_mix": "채널 믹스 변화",
            "weather": "외부 요인",
        }
        details = {
            "customer_count": f"객수 변화 {payload.customer_delta_pct:+.1f}%",
            "avg_ticket": f"객단가 변화 {payload.avg_ticket_delta_pct:+.1f}%",
            "channel_mix": f"채널 기여 {payload.channel_delta_pct:+.1f}%p",
            "weather": f"날씨 영향 {payload.weather_impact_pct:+.1f}%p",
        }
        factor_scores = factor_scores_from_deltas(
            customer_delta_pct=payload.customer_delta_pct,
            avg_ticket_delta_pct=payload.avg_ticket_delta_pct,
            channel_delta_pct=payload.channel_delta_pct,
            weather_impact_pct=payload.weather_impact_pct,
        )
        top_factor_keys = sorted(factor_scores, key=factor_scores.get, reverse=True)[:3]
        highlights = [
            f"{idx + 1}. {labels[key]}: {details[key]}" for idx, key in enumerate(top_factor_keys)
        ]

        context = (
            f"store_id={payload.store_id}\n"
            f"revenue_delta_pct={payload.revenue_delta_pct:+.1f}\n"
            f"customer_delta_pct={payload.customer_delta_pct:+.1f}\n"
            f"avg_ticket_delta_pct={payload.avg_ticket_delta_pct:+.1f}\n"
            f"channel_delta_pct={payload.channel_delta_pct:+.1f}\n"
            f"weather_impact_pct={payload.weather_impact_pct:+.1f}\n"
            f"top_factors={', '.join(labels[key] for key in top_factor_keys)}"
        )
        summary = self.prompt_service.render_analysis_summary(
            "sales_diagnostics",
            context=context,
            lead=(
                f"매출 {payload.revenue_delta_pct:+.1f}% 변화의 핵심 원인은 "
                f"{', '.join(labels[key] for key in top_factor_keys)}입니다."
            ),
        )
        summary = self.safety_service.mask_text(summary)
        self.safety_service.assert_policy_safe(summary)

        evidence = [
            self.evidence_service.build(
                metric="매출 증감",
                value=f"{payload.revenue_delta_pct:+.1f}%",
                period=f"{payload.data_window.start}~{payload.data_window.end}",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="객수 증감",
                value=f"{payload.customer_delta_pct:+.1f}%",
                period=f"{payload.data_window.start}~{payload.data_window.end}",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="객단가 증감",
                value=f"{payload.avg_ticket_delta_pct:+.1f}%",
                period=f"{payload.data_window.start}~{payload.data_window.end}",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
        ]

        if cold_start:
            highlights.append("콜드스타트 모드로 가능한 범위의 해석만 제공합니다.")

        return AnalysisResponse(
            store_id=payload.store_id,
            analysis_type="sales_diagnostics",
            summary=summary,
            highlights=highlights,
            evidence=evidence,
            warnings=warnings,
            version=self.governance_service.get_version("analysis"),
            cold_start_mode=cold_start,
        )

    def churn_insight(self, payload: ChurnInsightRequest) -> AnalysisResponse:
        warnings, cold_start = self.sufficiency_service.validate_analysis_input(payload)
        normalized_frequency = max(payload.at_risk_customers / 10, 1)
        features = ChurnFeatures(
            customer_id="segment",
            store_id=payload.store_id,
            recency=payload.delayed_visit_days,
            frequency=normalized_frequency,
            monetary=max(10000, payload.at_risk_customers * 2000),
            last_visit_days=payload.delayed_visit_days,
            coupon_use_rate=payload.coupon_redemption_rate,
        )
        churn_score = build_churn_score(features)
        severity = {"high": "높음", "medium": "중간", "low": "낮음"}[
            classify_churn_risk(churn_score)
        ]
        delay_ratio = payload.delayed_visit_days / payload.avg_visit_cycle_days
        context = (
            f"store_id={payload.store_id}\n"
            f"at_risk_customers={payload.at_risk_customers}\n"
            f"delay_ratio={delay_ratio:.2f}\n"
            f"churn_score={churn_score:.1f}\n"
            f"coupon_redemption_rate={payload.coupon_redemption_rate:.2f}"
        )
        summary = self.prompt_service.render_analysis_summary(
            "churn_insight",
            context=context,
            lead=(
                f"이탈 위험 고객 {payload.at_risk_customers}명은 평균 방문주기 대비 "
                f"{delay_ratio:.1f}배 지연되어 위험도 {severity}이며 이탈 점수는 {churn_score:.1f}점입니다."
            ),
        )
        summary = self.safety_service.mask_text(summary)
        self.safety_service.assert_policy_safe(summary)
        highlights = [
            f"방문주기 지연: {payload.delayed_visit_days:.1f}일",
            f"기준 방문주기: {payload.avg_visit_cycle_days:.1f}일",
            f"쿠폰 반응률: {payload.coupon_redemption_rate * 100:.1f}%",
            f"베이스라인 이탈 점수: {churn_score:.1f}",
        ]
        if cold_start:
            highlights.append("표본 부족으로 가설 중심 권고를 제공합니다.")
        evidence = [
            self.evidence_service.build(
                metric="이탈 위험 고객 수",
                value=str(payload.at_risk_customers),
                period=f"{payload.data_window.start}~{payload.data_window.end}",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="방문주기 지연",
                value=f"{payload.delayed_visit_days:.1f}일",
                period=f"{payload.data_window.start}~{payload.data_window.end}",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
        ]
        return AnalysisResponse(
            store_id=payload.store_id,
            analysis_type="churn_insight",
            summary=summary,
            highlights=highlights,
            evidence=evidence,
            warnings=warnings,
            version=self.governance_service.get_version("analysis"),
            cold_start_mode=cold_start,
        )

    def anomaly_explanation(self, payload: AnomalyExplanationRequest) -> AnalysisResponse:
        warnings, cold_start = self.sufficiency_service.validate_analysis_input(payload)
        hypothesis_map = {
            "payment": ["승인 취소 반복", "결제단말 오류", "수기 정산 누락"],
            "discount": ["과다 할인 권한 사용", "프로모션 룰 오적용", "직원 교육 미흡"],
            "inventory": ["폐기 누락", "보관 불량", "실사 계량 오류"],
            "point_leak": ["중복 적립", "비정상 회원 매핑", "수동 포인트 조정 남용"],
        }
        hypotheses = hypothesis_map[payload.anomaly_type]
        severity = classify_anomaly(payload.anomaly_score / 100)
        context = (
            f"store_id={payload.store_id}\n"
            f"anomaly_type={payload.anomaly_type}\n"
            f"anomaly_score={payload.anomaly_score:.1f}\n"
            f"severity={severity}\n"
            f"occurrence_count={payload.occurrence_count}\n"
            f"revenue_impact={payload.revenue_impact:,.0f}\n"
            f"hypotheses={', '.join(hypotheses)}"
        )
        summary = self.prompt_service.render_analysis_summary(
            "anomaly_explanation",
            context=context,
            lead=(
                f"{payload.anomaly_type} 이상점수 {payload.anomaly_score:.1f}점으로 심각도는 {severity}이며, "
                f"발생 {payload.occurrence_count}건에 대한 우선 가설은 {hypotheses[0]}입니다."
            ),
        )
        summary = self.safety_service.mask_text(summary)
        self.safety_service.assert_policy_safe(summary)
        highlights = [
            f"심각도: {severity}",
            f"가능 원인 1: {hypotheses[0]}",
            f"가능 원인 2: {hypotheses[1]}",
            f"가능 원인 3: {hypotheses[2]}",
            f"예상 영향액: {payload.revenue_impact:,.0f}원",
        ]
        if cold_start:
            highlights.append("이상 유형 설명은 제공되지만 재발 확률 추정은 생략됩니다.")
        evidence = [
            self.evidence_service.build(
                metric="이상 점수",
                value=f"{payload.anomaly_score:.1f}",
                period=f"{payload.data_window.start}~{payload.data_window.end}",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="발생 건수",
                value=str(payload.occurrence_count),
                period=f"{payload.data_window.start}~{payload.data_window.end}",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
        ]
        return AnalysisResponse(
            store_id=payload.store_id,
            analysis_type="anomaly_explanation",
            summary=summary,
            highlights=highlights,
            evidence=evidence,
            warnings=warnings,
            version=self.governance_service.get_version("analysis"),
            cold_start_mode=cold_start,
        )
