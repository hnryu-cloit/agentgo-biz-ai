from datetime import timedelta

from app.core.config import settings
from app.schemas.ai import BaseAnalysisRequest, RetentionOfferRequest, WarningMessage


class SufficiencyService:
    def validate_analysis_input(self, payload: BaseAnalysisRequest) -> tuple[list[WarningMessage], bool]:
        warnings: list[WarningMessage] = []
        days = (payload.data_window.end - payload.data_window.start).days + 1

        if days < settings.min_analysis_days:
            warnings.append(
                WarningMessage(
                    code="insufficient_period",
                    message=f"최소 {settings.min_analysis_days}일 데이터가 필요하지만 {days}일만 제공되었습니다.",
                )
            )
        if payload.record_count < settings.min_analysis_records:
            warnings.append(
                WarningMessage(
                    code="insufficient_records",
                    message=(
                        f"최소 {settings.min_analysis_records}건 데이터가 필요하지만 "
                        f"{payload.record_count}건만 제공되었습니다."
                    ),
                )
            )
        cold_start = bool(warnings)
        return warnings, cold_start

    def validate_retention_input(self, payload: RetentionOfferRequest) -> list[WarningMessage]:
        warnings: list[WarningMessage] = []
        if payload.customer_count < 30:
            warnings.append(
                WarningMessage(
                    code="small_segment",
                    message="세그먼트 표본이 작아 복귀율 추정 신뢰도가 낮습니다.",
                )
            )
        if payload.coupon_budget == 0:
            warnings.append(
                WarningMessage(
                    code="budget_missing",
                    message="예산이 0원이어서 쿠폰 대신 메시지 중심 전략으로 제한됩니다.",
                )
            )
        return warnings
