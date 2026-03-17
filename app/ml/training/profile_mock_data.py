from __future__ import annotations

import json
from pathlib import Path

from app.data.pipelines import profile_dataset


def main() -> None:
    mock_dir = Path(__file__).resolve().parents[2] / "mock_data"
    mapping = {
        "sales": mock_dir / "sales_daily.csv",
        "customer": mock_dir / "customer_rfm.csv",
        "review": mock_dir / "reviews.csv",
        "anomaly": mock_dir / "anomalies.csv",
        "menu": mock_dir / "menu_metrics.csv",
        "inventory": mock_dir / "inventory_monthly.csv",
        "staffing": mock_dir / "staffing_hourly.csv",
    }
    profiles = {dataset_type: profile_dataset(dataset_type, path) for dataset_type, path in mapping.items()}
    print(json.dumps(profiles, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
