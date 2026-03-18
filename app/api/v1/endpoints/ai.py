from fastapi import APIRouter, Depends, Body
from typing import List, Dict, Any
from app.services.analysis_service import AnalysisService

router = APIRouter()

@router.post("/analyze/menu-engineering")
async def analyze_menu(
    sales_data: List[Dict] = Body(...),
    lineup_data: List[Dict] = Body(...)
):
    """메뉴 엔지니어링 4분면 분석 API"""
    return await AnalysisService.analyze_menu_engineering(sales_data, lineup_data)

@router.post("/analyze/customer-churn")
async def analyze_churn(
    point_data: List[Dict] = Body(...)
):
    """고객 이탈 예측 및 RFM 분석 API"""
    return await AnalysisService.analyze_customer_churn(point_data)

@router.post("/analyze/full-dashboard")
async def analyze_full(
    sales_data: List[Dict] = Body(...),
    lineup_data: List[Dict] = Body(...),
    point_data: List[Dict] = Body(...),
    receipt_data: List[Dict] = Body(...)
):
    """지표 산출(ML) + 해석(Gemini) 통합 분석 API"""
    return await AnalysisService.analyze_full_dashboard(sales_data, lineup_data, point_data, receipt_data)

@router.post("/analyze/operational-anomalies")
async def analyze_anomaly(
    receipt_data: List[Dict] = Body(...)
):
    """운영 리스크 및 이상 탐지 API"""
    return await AnalysisService.analyze_operational_anomalies(receipt_data)
