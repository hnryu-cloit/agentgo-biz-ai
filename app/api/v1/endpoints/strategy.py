from fastapi import APIRouter

from app.schemas.ai import (
    CampaignBepSimulationRequest,
    CampaignBepSimulationResponse,
    CampaignUpliftRequest,
    CampaignUpliftResponse,
    MenuPricingRequest,
    MenuPricingResponse,
    RetentionOfferRequest,
    StrategyResponse,
)
from app.services.strategy_service import StrategyService

router = APIRouter()

_strategy_service = StrategyService()


@router.post("/strategy/retention-offer", response_model=StrategyResponse)
def retention_offer(payload: RetentionOfferRequest) -> StrategyResponse:
    """이탈 위험 고객 리텐션 오퍼 전략 추천 API"""
    return _strategy_service.retention_offer(payload)


@router.post("/strategy/menu-pricing", response_model=MenuPricingResponse)
def menu_pricing(payload: MenuPricingRequest) -> MenuPricingResponse:
    """메뉴 가격 조정 및 액션 전략 추천 API"""
    return _strategy_service.menu_pricing(payload)


@router.post("/strategy/campaign-bep", response_model=CampaignBepSimulationResponse)
def campaign_bep(payload: CampaignBepSimulationRequest) -> CampaignBepSimulationResponse:
    """캠페인 손익분기 시뮬레이션 API"""
    return _strategy_service.campaign_bep_simulation(payload)


@router.post("/strategy/campaign-uplift", response_model=CampaignUpliftResponse)
def campaign_uplift(payload: CampaignUpliftRequest) -> CampaignUpliftResponse:
    """캠페인 증분 효과 추정 API"""
    return _strategy_service.campaign_uplift_estimate(payload)