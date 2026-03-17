from __future__ import annotations

import csv
import json
from pathlib import Path

from app.ml.evaluation.metrics import precision_at_k
from app.ml.inference.baseline_models import predict_anomalies, to_dicts


def main() -> None:
    data_path = Path(__file__).resolve().parents[2] / "mock_data" / "anomalies.csv"
    predictions = predict_anomalies(data_path)

    labels: list[int] = []
    with open(data_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            labels.append(int(row["is_anomaly"]))

    scores = [item.anomaly_probability for item in predictions]
    summary = {
        "task": "anomaly_baseline",
        "row_count": len(predictions),
        "precision_at_2": precision_at_k(labels, scores, k=2),
        "predictions": to_dicts(predictions),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
