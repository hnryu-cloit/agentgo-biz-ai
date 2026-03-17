from datetime import datetime, timezone

from app.schemas.ai import GovernanceRegistryResponse, VersionTag


class GovernanceService:
    def __init__(self) -> None:
        self._versions = [
            VersionTag(
                agent="analysis",
                model_version="analysis-heuristic-0.1.0",
                prompt_version="analysis-prompt-0.1.0",
                postprocess_version="analysis-post-0.1.0",
            ),
            VersionTag(
                agent="strategy",
                model_version="strategy-heuristic-0.1.0",
                prompt_version="strategy-prompt-0.1.0",
                postprocess_version="strategy-post-0.1.0",
            ),
            VersionTag(
                agent="ocr",
                model_version="ocr-rule-0.1.0",
                prompt_version="ocr-summary-0.1.0",
                postprocess_version="ocr-checklist-0.1.0",
            ),
            VersionTag(
                agent="execution",
                model_version="execution-rule-0.1.0",
                prompt_version="execution-policy-0.1.0",
                postprocess_version="execution-post-0.1.0",
            ),
        ]

    def get_registry(self) -> GovernanceRegistryResponse:
        return GovernanceRegistryResponse(
            versions=self._versions,
            rollback_ready=True,
            changed_at=datetime.now(timezone.utc),
        )

    def get_version(self, agent: str) -> VersionTag:
        for version in self._versions:
            if version.agent == agent:
                return version
        raise KeyError(f"Unknown agent: {agent}")
