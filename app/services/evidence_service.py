from datetime import datetime

from app.schemas.ai import Evidence, SourceRef


class EvidenceService:
    def build(self, metric: str, value: str, period: str, source_name: str, uploaded_at: datetime) -> Evidence:
        return Evidence(
            metric=metric,
            value=value,
            period=period,
            source=SourceRef(name=source_name, uploaded_at=uploaded_at),
        )
