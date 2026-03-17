from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class MetricRecord:
    task: str
    version: str
    metric_name: str
    metric_value: float
    sample_size: int
    created_at: str


class MetricsRegistry:
    def __init__(self, registry_path: str | Path) -> None:
        self.registry_path = Path(registry_path)

    def load(self) -> list[MetricRecord]:
        if not self.registry_path.exists():
            return []
        with open(self.registry_path, encoding="utf-8") as handle:
            data = json.load(handle)
        return [MetricRecord(**item) for item in data]

    def append(self, record: MetricRecord) -> None:
        records = self.load()
        records.append(record)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w", encoding="utf-8") as handle:
            json.dump([asdict(item) for item in records], handle, ensure_ascii=False, indent=2)


def build_metric_record(
    task: str,
    version: str,
    metric_name: str,
    metric_value: float,
    sample_size: int,
) -> MetricRecord:
    return MetricRecord(
        task=task,
        version=version,
        metric_name=metric_name,
        metric_value=round(metric_value, 4),
        sample_size=sample_size,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
