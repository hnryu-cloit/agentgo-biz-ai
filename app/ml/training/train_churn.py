from __future__ import annotations

import csv
import json
from pathlib import Path

from app.ml.evaluation.metrics import accuracy
from app.ml.inference.baseline_models import predict_churn, to_dicts


def main() -> None:
    data_path = Path(__file__).resolve().parents[2] / "mock_data" / "customer_rfm.csv"
    predictions = predict_churn(data_path)

    labels: list[str] = []
    with open(data_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            labels.append("high" if int(row["churned"]) == 1 else "low")

    predicted_labels = [item.risk_level if item.risk_level != "medium" else "high" for item in predictions]
    summary = {
        "task": "churn_baseline",
        "row_count": len(predictions),
        "accuracy_proxy": accuracy(labels, predicted_labels),
        "predictions": to_dicts(predictions),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
