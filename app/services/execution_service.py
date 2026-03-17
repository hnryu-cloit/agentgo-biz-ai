from app.schemas.ai import (
    CampaignExecutionRequest,
    CampaignExecutionResponse,
    CampaignTargetExclusion,
    CampaignTargetValidationRequest,
    CampaignTargetValidationResponse,
)


class ExecutionService:
    def validate_targets(
        self, payload: CampaignTargetValidationRequest
    ) -> CampaignTargetValidationResponse:
        exclusions: list[CampaignTargetExclusion] = []
        for target in payload.targets:
            if not target.consent:
                exclusions.append(
                    CampaignTargetExclusion(customer_id=target.customer_id, reason="missing_consent")
                )
            elif target.cooldown_days < 7:
                exclusions.append(
                    CampaignTargetExclusion(customer_id=target.customer_id, reason="cooldown_active")
                )
            elif target.duplicate:
                exclusions.append(
                    CampaignTargetExclusion(customer_id=target.customer_id, reason="duplicate_target")
                )

        excluded_ids = {item.customer_id for item in exclusions}
        valid_count = sum(1 for target in payload.targets if target.customer_id not in excluded_ids)
        return CampaignTargetValidationResponse(
            campaign_id=payload.campaign_id,
            valid_count=valid_count,
            excluded_count=len(exclusions),
            exclusions=exclusions,
        )

    def execute_campaign(self, payload: CampaignExecutionRequest) -> CampaignExecutionResponse:
        if not payload.approved:
            return CampaignExecutionResponse(
                campaign_id=payload.campaign_id,
                status="pending_approval",
                retries=0,
                message="승인 전 단계이므로 실행이 보류되었습니다.",
            )

        if payload.dry_run:
            return CampaignExecutionResponse(
                campaign_id=payload.campaign_id,
                status="scheduled",
                retries=0,
                message=f"{payload.channel} 채널 발송이 dry-run으로 검증되었습니다.",
            )

        return CampaignExecutionResponse(
            campaign_id=payload.campaign_id,
            status="executed",
            retries=0,
            message=f"{payload.valid_target_count}건 발송을 실행 큐에 적재했습니다.",
        )
