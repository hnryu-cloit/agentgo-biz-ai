from __future__ import annotations

import json
from typing import Any

import pandas as pd

from app.ml.features.anomaly import AnomalyFeature
from app.ml.features.churn import ChurnFeature
from app.ml.features.menu import MenuEngineeringFeature
from app.ml.features.sales import SalesTrendFeature
from app.schemas.ai import (
    AnalysisResponse,
    AnomalyExplanationRequest,
    ChurnInsightRequest,
    SalesDiagnosticRequest,
)
from app.services.evidence_service import EvidenceService
from app.services.governance_service import GovernanceService
from app.services.safety_service import SafetyService
from app.services.sufficiency_service import SufficiencyService

try:
    from common.gemini import Gemini
except Exception:  # pragma: no cover - optional runtime dependency
    Gemini = None


class AnalysisService:
    def __init__(self) -> None:
        self.evidence_service = EvidenceService()
        self.governance_service = GovernanceService()
        self.safety_service = SafetyService()
        self.sufficiency_service = SufficiencyService()

    def sales_diagnostics(self, payload: SalesDiagnosticRequest) -> AnalysisResponse:
        warnings, cold_start = self.sufficiency_service.validate_analysis_input(payload)

        traffic_impact = payload.customer_delta_pct * 0.45
        ticket_impact = payload.avg_ticket_delta_pct * 0.35
        channel_impact = payload.channel_delta_pct * 0.15
        weather_impact = payload.weather_impact_pct * 0.05
        composite_gap = traffic_impact + ticket_impact + channel_impact + weather_impact

        drivers = [
            ("방문객 수", payload.customer_delta_pct),
            ("객단가", payload.avg_ticket_delta_pct),
            ("채널 믹스", payload.channel_delta_pct),
            ("날씨 영향", payload.weather_impact_pct),
        ]
        drivers.sort(key=lambda item: abs(item[1]), reverse=True)

        direction = "상승" if payload.revenue_delta_pct >= 0 else "하락"
        summary = (
            f"매출은 전기 대비 {payload.revenue_delta_pct:+.1f}% {direction}했습니다. "
            f"가장 큰 요인은 {drivers[0][0]} {drivers[0][1]:+.1f}%이며, "
            f"복합 영향 점수는 {composite_gap:+.1f}입니다."
        )
        summary = self.safety_service.mask_text(summary)
        self.safety_service.assert_policy_safe(summary)

        highlights = [
            f"{name} 변동 {value:+.1f}%"
            for name, value in drivers[:3]
        ]
        if payload.revenue_delta_pct < 0:
            highlights.append("저조 시간대 판촉과 채널별 가격 구성을 함께 점검하세요.")
        else:
            highlights.append("증가한 유입이 재방문으로 이어지는지 회원 전환율을 확인하세요.")

        evidence = [
            self.evidence_service.build(
                metric="매출 증감률",
                value=f"{payload.revenue_delta_pct:+.1f}%",
                period=f"{payload.data_window.start}~{payload.data_window.end}",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="방문객 증감률",
                value=f"{payload.customer_delta_pct:+.1f}%",
                period=f"{payload.data_window.start}~{payload.data_window.end}",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="객단가 증감률",
                value=f"{payload.avg_ticket_delta_pct:+.1f}%",
                period=f"{payload.data_window.start}~{payload.data_window.end}",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
        ]
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

        cycle_ratio = payload.delayed_visit_days / payload.avg_visit_cycle_days
        risk_band = "high" if cycle_ratio >= 1.6 else "medium" if cycle_ratio >= 1.2 else "low"
        save_rate = max(0.0, min(0.9, payload.coupon_redemption_rate * (1.1 if risk_band == "high" else 0.95)))

        summary = (
            f"이탈 위험 고객은 {payload.at_risk_customers:,}명이며 방문 지연은 평균 주기의 {cycle_ratio:.1f}배입니다. "
            f"위험도는 {risk_band}로 판단되며 현재 쿠폰 반응률 기준 예상 방어율은 {save_rate * 100:.1f}%입니다."
        )
        summary = self.safety_service.mask_text(summary)
        self.safety_service.assert_policy_safe(summary)

        highlights = [
            f"이탈 위험 고객 {payload.at_risk_customers:,}명",
            f"방문 지연 {payload.delayed_visit_days:.1f}일, 평균 주기 {payload.avg_visit_cycle_days:.1f}일",
            f"쿠폰 반응률 {payload.coupon_redemption_rate * 100:.1f}%",
        ]
        if risk_band == "high":
            highlights.append("7일 이내 복귀 오퍼와 미반응 고객 재접촉 시나리오를 병행하세요.")

        evidence = [
            self.evidence_service.build(
                metric="이탈 위험 고객 수",
                value=f"{payload.at_risk_customers:,}명",
                period=f"{payload.data_window.start}~{payload.data_window.end}",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="평균 방문 지연",
                value=f"{payload.delayed_visit_days:.1f}일",
                period="최근 방문 기준",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="쿠폰 반응률",
                value=f"{payload.coupon_redemption_rate * 100:.1f}%",
                period="최근 캠페인 기준",
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

        severity = "high" if payload.anomaly_score >= 80 else "medium" if payload.anomaly_score >= 50 else "low"
        summary = (
            f"{payload.anomaly_type} 이상이 {payload.occurrence_count}건 감지됐고 이상 점수는 {payload.anomaly_score:.1f}점입니다. "
            f"예상 매출 영향은 {payload.revenue_impact:,.0f}원이며 대응 우선순위는 {severity}입니다."
        )
        summary = self.safety_service.mask_text(summary)
        self.safety_service.assert_policy_safe(summary)

        highlights = [
            f"이상 유형: {payload.anomaly_type}",
            f"발생 건수: {payload.occurrence_count}건",
            f"매출 영향: {payload.revenue_impact:,.0f}원",
        ]
        if severity == "high":
            highlights.append("원장 대조와 승인 로그 점검을 같은 날 안에 완료해야 합니다.")

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
                value=f"{payload.occurrence_count}건",
                period=f"{payload.data_window.start}~{payload.data_window.end}",
                source_name=payload.source_name,
                uploaded_at=payload.uploaded_at,
            ),
            self.evidence_service.build(
                metric="매출 영향",
                value=f"{payload.revenue_impact:,.0f}원",
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

    @staticmethod
    async def analyze_full_dashboard(
        sales_data: list[dict[str, Any]],
        lineup_data: list[dict[str, Any]],
        point_data: list[dict[str, Any]],
        receipt_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        sales_analysis = SalesTrendFeature.analyze_hourly_trends(pd.DataFrame(sales_data))
        menu_analysis = await AnalysisService.analyze_menu_engineering(sales_data, lineup_data)
        churn_analysis = await AnalysisService.analyze_customer_churn(point_data)
        anomaly_analysis = await AnalysisService.analyze_operational_anomalies(receipt_data)

        context = {
            "sales_summary": sales_analysis.get("summary"),
            "menu_summary": menu_analysis.get("summary"),
            "churn_summary": churn_analysis.get("summary"),
            "risk_score": anomaly_analysis.get("summary", {}).get("anomaly_score_max", 0),
        }
        ai_interpretation = AnalysisService._generate_ai_interpretation(context)

        return {
            "sales_trend": sales_analysis,
            "menu_strategy": menu_analysis,
            "customer_intelligence": churn_analysis,
            "operational_risk": anomaly_analysis,
            "ai_reasoning": ai_interpretation,
            "ai_meta": {
                "generated_at": pd.Timestamp.now().isoformat(),
                "engine": "Gemini-2.0-Flash + ML-Baseline",
            },
        }

    @staticmethod
    async def analyze_menu_engineering(
        sales_data: list[dict[str, Any]],
        lineup_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        sales_df = pd.DataFrame(sales_data)
        lineup_df = pd.DataFrame(lineup_data)
        if sales_df.empty or lineup_df.empty:
            return {
                "menu_matrix": [],
                "ai_insights": [],
                "summary": {
                    "star_count": 0,
                    "plowhorse_count": 0,
                    "puzzle_count": 0,
                    "dog_count": 0,
                },
            }

        processed_df = MenuEngineeringFeature.calculate_metrics(sales_df, lineup_df)
        analyzed_df = MenuEngineeringFeature.categorize_menu(processed_df)

        stars = analyzed_df[analyzed_df["category"] == "Star"]
        plowhorses = analyzed_df[analyzed_df["category"] == "Plowhorse"]
        puzzles = analyzed_df[analyzed_df["category"] == "Puzzle"]
        dogs = analyzed_df[analyzed_df["category"] == "Dog"]

        insights: list[dict[str, str]] = []
        if not stars.empty:
            top_star = stars.sort_values(by="qty", ascending=False).iloc[0]
            insights.append(
                {
                    "type": "success",
                    "title": f"효자 메뉴 '{top_star['menu_name']}' 유지",
                    "description": "판매량과 마진이 모두 우수합니다. 현재 품질과 노출 우선순위를 유지하세요.",
                }
            )
        if not plowhorses.empty:
            top_plow = plowhorses.sort_values(by="qty", ascending=False).iloc[0]
            insights.append(
                {
                    "type": "warning",
                    "title": f"식사 메뉴 '{top_plow['menu_name']}' 수익성 개선",
                    "description": "판매량 대비 단위마진이 낮습니다. 세트 구성이나 가격 미세 조정을 검토하세요.",
                }
            )
        if not puzzles.empty:
            top_puzzle = puzzles.sort_values(by="unit_margin", ascending=False).iloc[0]
            insights.append(
                {
                    "type": "info",
                    "title": f"수수께끼 메뉴 '{top_puzzle['menu_name']}' 판매 촉진",
                    "description": "마진은 높지만 노출이 부족합니다. 추천 영역 배치와 직원 권유 멘트를 강화하세요.",
                }
            )
        if not dogs.empty:
            insights.append(
                {
                    "type": "danger",
                    "title": "비효율 메뉴 정비",
                    "description": f"인기도와 수익성이 모두 낮은 메뉴 {len(dogs)}개에 대해 유지 필요성을 재검토하세요.",
                }
            )

        return {
            "menu_matrix": analyzed_df.to_dict(orient="records"),
            "ai_insights": insights,
            "summary": {
                "star_count": len(stars),
                "plowhorse_count": len(plowhorses),
                "puzzle_count": len(puzzles),
                "dog_count": len(dogs),
            },
        }

    @staticmethod
    async def analyze_customer_churn(point_data: list[dict[str, Any]]) -> dict[str, Any]:
        point_df = pd.DataFrame(point_data)
        if point_df.empty:
            return {
                "customer_segments": [],
                "ai_insights": [],
                "summary": {
                    "vip_count": 0,
                    "at_risk_count": 0,
                    "lost_count": 0,
                    "new_count": 0,
                    "loyal_count": 0,
                },
            }

        rfm_df = ChurnFeature.calculate_rfm(point_df)
        segmented_df = ChurnFeature.segment_customers(rfm_df)

        at_risk = segmented_df[segmented_df["segment"] == "At Risk"]
        vips = segmented_df[segmented_df["segment"] == "VIP"]
        lost = segmented_df[segmented_df["segment"] == "Lost"]

        insights: list[dict[str, str]] = []
        if not at_risk.empty:
            insights.append(
                {
                    "type": "danger",
                    "title": f"이탈 위험 고객 {len(at_risk)}명 감지",
                    "description": "방문 주기가 길어진 고객군입니다. 복귀 오퍼와 개인화 메시지를 우선 발송하세요.",
                }
            )
        if not vips.empty:
            insights.append(
                {
                    "type": "success",
                    "title": f"VIP 고객 {len(vips)}명 유지 중",
                    "description": "고기여 고객군입니다. 경험 악화를 막기 위한 우선 응대가 필요합니다.",
                }
            )
        if not lost.empty:
            insights.append(
                {
                    "type": "info",
                    "title": f"이탈 고객 {len(lost)}명 회복 제안",
                    "description": "90일 이상 미방문 고객입니다. 마지막 구매 메뉴 기반 오퍼가 적합합니다.",
                }
            )

        return {
            "customer_segments": segmented_df.to_dict(orient="records"),
            "ai_insights": insights,
            "summary": {
                "vip_count": len(vips),
                "at_risk_count": len(at_risk),
                "lost_count": len(lost),
                "new_count": len(segmented_df[segmented_df["segment"] == "New"]),
                "loyal_count": len(segmented_df[segmented_df["segment"] == "Loyal"]),
            },
        }

    @staticmethod
    async def analyze_operational_anomalies(receipt_data: list[dict[str, Any]]) -> dict[str, Any]:
        receipt_df = pd.DataFrame(receipt_data)
        if receipt_df.empty:
            return {
                "anomaly_stats": [],
                "high_risk_receipts": [],
                "ai_insights": [],
                "summary": {
                    "anomaly_score_max": 0.0,
                    "high_risk_count": 0,
                    "total_cancel_count": 0,
                },
            }

        anomaly_df = AnomalyFeature.detect_cancellation_anomalies(receipt_df)
        high_risk_receipts = AnomalyFeature.identify_high_risk_receipts(receipt_df)

        risky_items = high_risk_receipts.to_dict(orient="records")
        serious_anomalies = anomaly_df[anomaly_df["anomaly_score"] > 2.0]

        insights: list[dict[str, str]] = []
        if not serious_anomalies.empty:
            peak_anomaly = serious_anomalies.sort_values(by="anomaly_score", ascending=False).iloc[0]
            insights.append(
                {
                    "type": "danger",
                    "title": f"비정상 취소율 급증 감지 ({int(peak_anomaly['hour'])}시)",
                    "description": "평균 대비 취소율이 크게 높습니다. 해당 시간대 영수증과 취소 사유를 점검하세요.",
                }
            )
        if risky_items:
            insights.append(
                {
                    "type": "warning",
                    "title": f"고액 취소 영수증 {len(risky_items)}건 발견",
                    "description": "평균 결제액 대비 큰 취소 건입니다. 오입력과 부정 사용 가능성을 함께 확인하세요.",
                }
            )
        if not insights:
            insights.append(
                {
                    "type": "success",
                    "title": "운영 리스크 정상",
                    "description": "최근 결제 및 취소 패턴에서 뚜렷한 이상 징후가 없습니다.",
                }
            )

        return {
            "anomaly_stats": anomaly_df.to_dict(orient="records"),
            "high_risk_receipts": risky_items,
            "ai_insights": insights,
            "summary": {
                "anomaly_score_max": round(float(anomaly_df["anomaly_score"].max()), 2) if not anomaly_df.empty else 0.0,
                "high_risk_count": len(risky_items),
                "total_cancel_count": int(anomaly_df["cancel_count"].sum()) if "cancel_count" in anomaly_df else 0,
            },
        }

    @staticmethod
    def _generate_ai_interpretation(context: dict[str, Any]) -> dict[str, str]:
        fallback = {
            "headline": "매장 운영 데이터 통합 분석",
            "reasoning": "현재 매출과 고객 흐름을 종합하면 핵심 지표는 안정권이지만, 세부 카테고리 최적화 여지가 남아 있습니다.",
            "action_item": "피크 시간대 운영 품질을 유지하면서 저성과 메뉴와 이탈 위험 고객 대응을 우선 실행하세요.",
        }
        if Gemini is None:
            return fallback

        prompt = f"""
너는 정통 중식 파인 다이닝 브랜드 '크리스탈 제이드(Crystal Jade)'의 운영 전문 AI 컨설턴트야.
아래의 실시간 매장 지표를 보고, 브랜드 가치를 유지하면서 수익성을 높일 수 있는 오늘의 전략을 작성해줘.

데이터: {json.dumps(context, ensure_ascii=False)}

응답은 반드시 아래 JSON 형식으로만 해줘:
{{"headline": "전략 제목", "reasoning": "데이터 기반 원인 해석", "action_item": "당장 실행할 것"}}
""".strip()
        system_prompt = (
            "너는 글로벌 중식 브랜드 '크리스탈 제이드'의 성장을 돕는 전략 분석가야. "
            "고급스러운 미식 경험과 효율적인 매장 운영 사이의 최적점을 찾아야 해."
        )

        try:
            gemini = Gemini()
            raw = gemini.generate_gemini_content(prompt, system_prompt=system_prompt)
            parsed = json.loads(raw.strip("`json\n "))
            if all(key in parsed for key in ("headline", "reasoning", "action_item")):
                return parsed
        except Exception:
            pass
        return fallback
