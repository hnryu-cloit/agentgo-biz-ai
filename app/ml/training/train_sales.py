from __future__ import annotations

import json
from pathlib import Path

from app.ml.inference.baseline_models import predict_sales_factors, to_dicts


def main() -> None:
    data_path = Path(__file__).resolve().parents[2] / "mock_data" / "sales_daily.csv"
    predictions = predict_sales_factors(data_path)
    summary = {
        "task": "sales_factor_baseline",
        "store_count": len(predictions),
        "predictions": to_dicts(predictions),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
