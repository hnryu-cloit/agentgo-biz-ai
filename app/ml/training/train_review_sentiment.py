from __future__ import annotations

import csv
import json
from pathlib import Path

from app.ml.evaluation.metrics import accuracy
from app.ml.inference.baseline_models import predict_review_sentiment, to_dicts


def main() -> None:
    data_path = Path(__file__).resolve().parents[2] / "mock_data" / "reviews.csv"
    predictions = predict_review_sentiment(data_path)

    labels: list[str] = []
    with open(data_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            labels.append(row["sentiment_label"])

    predicted_labels = [item.sentiment for item in predictions]
    summary = {
        "task": "review_sentiment_baseline",
        "row_count": len(predictions),
        "accuracy": accuracy(labels, predicted_labels),
        "predictions": to_dicts(predictions),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
