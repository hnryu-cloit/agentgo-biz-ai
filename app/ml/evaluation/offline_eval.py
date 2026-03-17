from __future__ import annotations

import csv
from pathlib import Path

from app.ml.evaluation.metrics import accuracy, precision_at_k
from app.ml.evaluation.registry import MetricsRegistry, build_metric_record
from app.ml.inference.baseline_models import (
    predict_anomalies,
    predict_churn,
    predict_review_sentiment,
)


def evaluate_review_sentiment(data_path: str | Path) -> tuple[float, int]:
    predictions = predict_review_sentiment(data_path)
    with open(data_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        labels = [row["sentiment_label"] for row in reader]
    predicted = [item.sentiment for item in predictions]
    return accuracy(labels, predicted), len(labels)


def evaluate_churn(data_path: str | Path) -> tuple[float, int]:
    predictions = predict_churn(data_path)
    with open(data_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        labels = ["high" if int(row["churned"]) == 1 else "low" for row in reader]
    predicted = [item.risk_level if item.risk_level != "medium" else "high" for item in predictions]
    return accuracy(labels, predicted), len(labels)


def evaluate_anomaly(data_path: str | Path) -> tuple[float, int]:
    predictions = predict_anomalies(data_path)
    with open(data_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        labels = [int(row["is_anomaly"]) for row in reader]
    scores = [item.anomaly_probability for item in predictions]
    k = min(2, len(scores))
    return precision_at_k(labels, scores, k=k), len(labels)


def run_offline_evaluation(
    registry_path: str | Path,
    mock_data_dir: str | Path,
    version: str = "baseline-0.1.0",
) -> list[dict[str, float | int | str]]:
    registry = MetricsRegistry(registry_path)
    mock_dir = Path(mock_data_dir)

    results = []

    review_score, review_size = evaluate_review_sentiment(mock_dir / "reviews.csv")
    registry.append(
        build_metric_record("review_sentiment", version, "accuracy", review_score, review_size)
    )
    results.append({"task": "review_sentiment", "metric": "accuracy", "value": review_score})

    churn_score, churn_size = evaluate_churn(mock_dir / "customer_rfm.csv")
    registry.append(build_metric_record("churn", version, "accuracy_proxy", churn_score, churn_size))
    results.append({"task": "churn", "metric": "accuracy_proxy", "value": churn_score})

    anomaly_score, anomaly_size = evaluate_anomaly(mock_dir / "anomalies.csv")
    registry.append(build_metric_record("anomaly", version, "precision_at_2", anomaly_score, anomaly_size))
    results.append({"task": "anomaly", "metric": "precision_at_2", "value": anomaly_score})

    return results
