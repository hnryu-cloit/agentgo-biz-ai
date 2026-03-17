from __future__ import annotations

import json
from pathlib import Path

from app.ml.evaluation.offline_eval import run_offline_evaluation


def main() -> None:
    app_dir = Path(__file__).resolve().parents[2]
    results = run_offline_evaluation(
        registry_path=app_dir / "ml" / "evaluation" / "metrics_registry.json",
        mock_data_dir=app_dir / "mock_data",
        version="baseline-0.1.0",
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
