from fastapi import APIRouter

from app.schemas.ai import (
    InventoryOptimizationRequest,
    InventoryOptimizationResponse,
    StaffingOptimizationRequest,
    StaffingOptimizationResponse,
)
from app.services.operations_service import OperationsService

router = APIRouter()

_operations_service = OperationsService()


@router.post("/operations/staffing", response_model=StaffingOptimizationResponse)
def staffing_optimization(payload: StaffingOptimizationRequest) -> StaffingOptimizationResponse:
    """시간대별 인력 부족/과잉 감지 및 기회손실 산출 API"""
    return _operations_service.staffing_optimization(payload)


@router.post("/operations/inventory", response_model=InventoryOptimizationResponse)
def inventory_optimization(payload: InventoryOptimizationRequest) -> InventoryOptimizationResponse:
    """재고 손실 감지 및 발주 권장량 산출 API"""
    return _operations_service.inventory_optimization(payload)