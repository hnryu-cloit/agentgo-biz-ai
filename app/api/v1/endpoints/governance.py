from fastapi import APIRouter

from app.schemas.ai import GovernanceRegistryResponse, VersionTag
from app.services.governance_service import GovernanceService

router = APIRouter()

_governance_service = GovernanceService()


@router.get("/governance/registry", response_model=GovernanceRegistryResponse)
def get_registry() -> GovernanceRegistryResponse:
    """모델/프롬프트 버전 레지스트리 조회 API"""
    return _governance_service.get_registry()


@router.get("/governance/version/{agent}", response_model=VersionTag)
def get_version(agent: str) -> VersionTag:
    """에이전트별 버전 정보 조회 API"""
    return _governance_service.get_version(agent)