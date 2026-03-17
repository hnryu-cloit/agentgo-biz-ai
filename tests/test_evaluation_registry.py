from pathlib import Path

from app.ml.evaluation.offline_eval import run_offline_evaluation
from app.ml.evaluation.registry import MetricsRegistry


def test_offline_evaluation_writes_registry(tmp_path: Path) -> None:
    registry_path = tmp_path / "metrics_registry.json"
    mock_data_dir = Path("app/mock_data")

    results = run_offline_evaluation(
        registry_path=registry_path,
        mock_data_dir=mock_data_dir,
        version="baseline-test",
    )

    assert len(results) == 3

    registry = MetricsRegistry(registry_path)
    records = registry.load()
    assert len(records) == 3
    assert {record.task for record in records} == {"review_sentiment", "churn", "anomaly"}
