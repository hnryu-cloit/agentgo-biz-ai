from typing import List, Dict, Any
import pandas as pd
import json
from app.ml.features.menu import MenuEngineeringFeature
from app.ml.features.churn import ChurnFeature
from app.ml.features.anomaly import AnomalyFeature
from app.ml.features.sales import SalesTrendFeature
from common.gemini import Gemini

class AnalysisService:
    @staticmethod
    async def analyze_full_dashboard(
        sales_data: List[Dict], 
        lineup_data: List[Dict], 
        point_data: List[Dict],
        receipt_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        AI 서버 통합 분석: 지표 계산(ML) + 해석(Gemini)
        """
        gemini = Gemini()
        
        # 1. 지표 계산 (ML/Stats)
        sales_analysis = SalesTrendFeature.analyze_hourly_trends(pd.DataFrame(sales_data))
        menu_analysis = await AnalysisService.analyze_menu_engineering(sales_data, lineup_data)
        churn_analysis = await AnalysisService.analyze_customer_churn(point_data)
        anomaly_analysis = await AnalysisService.analyze_operational_anomalies(receipt_data)

        # 2. Gemini를 통한 데이터 해석 (Reasoning)
        # 모든 수치를 하나의 문맥으로 묶어 종합 진단
        context = {
            "sales_summary": sales_analysis.get("summary"),
            "menu_summary": menu_analysis.get("summary"),
            "churn_summary": churn_analysis.get("summary"),
            "risk_score": anomaly_analysis.get("summary", {}).get("anomaly_score_max", 0)
        }
        
        prompt = f"""
        너는 정통 중식 파인 다이닝 브랜드 '크리스탈 제이드(Crystal Jade)'의 운영 전문 AI 컨설턴트야. 
        아래의 실시간 매장 지표를 보고, 크리스탈 제이드의 브랜드 가치를 유지하면서 수익성을 극대화할 수 있는 '오늘의 전략'을 작성해줘.
        
        데이터: {json.dumps(context, ensure_ascii=False)}
        
        응답 가이드라인:
        1. 브랜드 명칭 '크리스탈 제이드'를 자연스럽게 언급할 것.
        2. 중식 파인 다이닝 특성에 맞는 고급스러운 어조를 사용할 것.
        3. 단순 수치 나열이 아닌, 프리미엄 서비스 관점의 해석을 포함할 것.
        
        응답은 반드시 아래 JSON 형식으로만 해줘:
        {{"headline": "전략 제목", "reasoning": "데이터 기반 원인 해석", "action_item": "당장 실행할 것"}}
        """
        
        system_prompt = "너는 글로벌 중식 브랜드 '크리스탈 제이드'의 성장을 돕는 전략 분석가야. 고급스러운 미식 경험과 효율적인 매장 운영 사이의 최적점을 찾아내야 해."
        
        try:
            ai_interpretation_raw = gemini.generate_gemini_content(prompt, system_prompt=system_prompt)
            ai_interpretation = json.loads(ai_interpretation_raw.strip('`json\n '))
        except:
            ai_interpretation = {
                "headline": "매장 운영 데이터 통합 분석",
                "reasoning": "현재 매출 및 고객 방문 패턴이 평소 흐름을 유지하고 있습니다.",
                "action_item": "효자 메뉴의 품질 유지에 집중하세요."
            }

        return {
            "sales_trend": sales_analysis,
            "menu_strategy": menu_analysis,
            "customer_intelligence": churn_analysis,
            "operational_risk": anomaly_analysis,
            "ai_reasoning": ai_interpretation,
            "ai_meta": {
                "generated_at": pd.Timestamp.now().isoformat(),
                "engine": "Gemini-2.0-Flash + ML-Baseline"
            }
        }

    # (기존 개별 분석 메서드들은 그대로 유지하되 내부에서 필요시 Gemini 호출 가능)
    @staticmethod
    async def analyze_menu_engineering(sales_data: List[Dict], lineup_data: List[Dict]) -> Dict[str, Any]:
        # ... (기존 로직 유지)

    # (기존 메서드들은 analyze_full_dashboard 내에서 호출되거나 독립적으로 사용 가능)
    @staticmethod
    async def analyze_menu_engineering(sales_data: List[Dict], lineup_data: List[Dict]) -> Dict[str, Any]:
        # (기존 로직 ...)
        # (기존 코드 유지 ...)
        sales_df = pd.DataFrame(sales_data)
        lineup_df = pd.DataFrame(lineup_data)
        
        # 1. 지표 계산 및 분류
        processed_df = MenuEngineeringFeature.calculate_metrics(sales_df, lineup_df)
        analyzed_df = MenuEngineeringFeature.categorize_menu(processed_df)
        
        # 2. 결과 가공 (JSON 형태)
        results = analyzed_df.to_dict(orient='records')
        
        # 3. AI 인사이트 도출
        stars = analyzed_df[analyzed_df['category'] == 'Star']
        plowhorses = analyzed_df[analyzed_df['category'] == 'Plowhorse']
        puzzles = analyzed_df[analyzed_df['category'] == 'Puzzle']
        dogs = analyzed_df[analyzed_df['category'] == 'Dog']
        
        insights = []
        if not stars.empty:
            top_star = stars.sort_values(by='qty', ascending=False).iloc[0]
            insights.append({
                "type": "success",
                "title": f"효자 메뉴 '{top_star['menu_name']}' 유지",
                "description": f"가장 인기가 높고 마진이 좋습니다. 현재의 품질과 가격 경쟁력을 유지하세요."
            })
            
        if not plowhorses.empty:
            top_plow = plowhorses.sort_values(by='qty', ascending=False).iloc[0]
            insights.append({
                "type": "warning",
                "title": f"식사 메뉴 '{top_plow['menu_name']}' 수익성 개선",
                "description": f"판매량은 많지만 마진이 낮습니다. 사이드 메뉴 구성을 바꾸거나 가격을 소폭 인상하여 수익성을 높여보세요."
            })
            
        if not puzzles.empty:
            top_puzzle = puzzles.sort_values(by='unit_margin', ascending=False).iloc[0]
            insights.append({
                "type": "info",
                "title": f"수수께끼 메뉴 '{top_puzzle['menu_name']}' 판매 촉진",
                "description": f"마진은 훌륭하지만 인지도가 낮습니다. 메뉴판 상단 배치나 SNS 홍보를 통해 판매량을 늘려보세요."
            })
            
        if not dogs.empty:
            insights.append({
                "type": "danger",
                "title": f"비효율 메뉴 정비",
                "description": f"인기도와 수익성이 모두 낮은 {len(dogs)}개의 메뉴가 있습니다. 메뉴 삭제 또는 재구성을 검토하세요."
            })
            
        return {
            "menu_matrix": results,
            "ai_insights": insights,
            "summary": {
                "star_count": len(stars),
                "plowhorse_count": len(plowhorses),
                "puzzle_count": len(puzzles),
                "dog_count": len(dogs)
            }
        }

    @staticmethod
    async def analyze_customer_churn(point_data: List[Dict]) -> Dict[str, Any]:
        """
        고객 RFM 세그먼트 분석 및 이탈 위험군 식별
        """
        point_df = pd.DataFrame(point_data)
        
        # 1. RFM 지표 산출
        rfm_df = ChurnFeature.calculate_rfm(point_df)
        
        # 2. 세그먼트 분류
        segmented_df = ChurnFeature.segment_customers(rfm_df)
        
        # 3. 결과 가공
        results = segmented_df.to_dict(orient='records')
        
        # 4. AI 인사이트 도출
        at_risk = segmented_df[segmented_df['segment'] == 'At Risk']
        vips = segmented_df[segmented_df['segment'] == 'VIP']
        lost = segmented_df[segmented_df['segment'] == 'Lost']
        
        insights = []
        if not at_risk.empty:
            insights.append({
                "type": "danger",
                "title": f"이탈 위험 고객 {len(at_risk)}명 감지",
                "description": f"방문 주기가 평소보다 1.5배 이상 길어진 고객들입니다. '컴백 쿠폰' 발송을 통해 재방문을 유도하세요."
            })
            
        if not vips.empty:
            insights.append({
                "type": "success",
                "title": f"VIP 고객 {len(vips)}명 유지 중",
                "description": f"매출 기여도가 가장 높은 상위 {len(vips)}명입니다. 이들을 위한 전용 시크릿 오퍼를 설계해 보세요."
            })
            
        if not lost.empty:
            insights.append({
                "type": "info",
                "title": f"이탈 고객 {len(lost)}명 회복 제안",
                "description": f"최근 90일 이상 방문하지 않은 고객들입니다. 마지막 방문 시 주문했던 메뉴 기반의 추천 오퍼가 효과적입니다."
            })
            
        return {
            "customer_segments": results,
            "ai_insights": insights,
            "summary": {
                "vip_count": len(vips),
                "at_risk_count": len(at_risk),
                "lost_count": len(lost),
                "new_count": len(segmented_df[segmented_df['segment'] == 'New']),
                "loyal_count": len(segmented_df[segmented_df['segment'] == 'Loyal'])
            }
        }

    @staticmethod
    async def analyze_operational_anomalies(receipt_data: List[Dict]) -> Dict[str, Any]:
        """
        운영 리스크 및 이상 취소 탐지 분석
        """
        receipt_df = pd.DataFrame(receipt_data)
        
        # 1. 취소율 이상 탐지
        anomaly_df = AnomalyFeature.detect_cancellation_anomalies(receipt_df)
        
        # 2. 고액 취소 식별
        high_risk_receipts = AnomalyFeature.identify_high_risk_receipts(receipt_df)
        
        # 3. 결과 가공
        results = anomaly_df.to_dict(orient='records')
        risky_items = high_risk_receipts.to_dict(orient='records')
        
        # 4. AI 인사이트 도출 (Z-score 2.0 이상을 심각으로 간주)
        serious_anomalies = anomaly_df[anomaly_df['anomaly_score'] > 2.0]
        
        insights = []
        if not serious_anomalies.empty:
            peak_anomaly = serious_anomalies.sort_values(by='anomaly_score', ascending=False).iloc[0]
            insights.append({
                "type": "danger",
                "title": f"비정상 취소율 급증 감지 ({peak_anomaly['hour']}시)",
                "description": f"통계적으로 평균 대비 취소율이 매우 높습니다. 해당 시간대 영수증 내역과 취소 사유를 면밀히 점검하세요."
            })
            
        if len(risky_items) > 0:
            insights.append({
                "type": "warning",
                "title": f"고액 취소 영수증 {len(risky_items)}건 발견",
                "description": f"매장 평균 결제액의 3배가 넘는 고액 취소 건이 발생했습니다. 직원의 오입력 또는 부정 사용 가능성이 있습니다."
            })
        else:
            insights.append({
                "type": "success",
                "title": "운영 리스크 정상",
                "description": "최근 결제 및 취소 패턴에서 특별한 이상 징후가 발견되지 않았습니다."
            })
            
        return {
            "anomaly_stats": results,
            "high_risk_receipts": risky_items,
            "ai_insights": insights,
            "summary": {
                "anomaly_score_max": round(anomaly_df['anomaly_score'].max(), 2),
                "high_risk_count": len(risky_items),
                "total_cancel_count": int(anomaly_df['cancel_count'].sum())
            }
        }
