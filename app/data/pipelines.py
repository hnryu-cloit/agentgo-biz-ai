from __future__ import annotations

from pathlib import Path

from app.data.loaders import load_csv_rows
from app.data.preprocessors import (
    preprocess_anomaly_row,
    preprocess_customer_row,
    preprocess_inventory_row,
    preprocess_menu_row,
    preprocess_review_row,
    preprocess_sales_row,
    preprocess_staffing_row,
)
from app.data.profilers import missing_fields, profile_numeric


PREPROCESSORS = {
    "sales": (preprocess_sales_row, ["date", "store_id", "revenue", "customers", "avg_ticket"]),
    "customer": (
        preprocess_customer_row,
        ["customer_id", "store_id", "recency", "frequency", "monetary"],
    ),
    "review": (preprocess_review_row, ["review_id", "store_id", "rating", "review_text"]),
    "anomaly": (preprocess_anomaly_row, ["event_id", "store_id", "event_type", "amount"]),
    "menu": (preprocess_menu_row, ["menu_id", "store_id", "price", "cost", "margin_rate"]),
    "inventory": (
        preprocess_inventory_row,
        ["month", "store_id", "item_id", "system_qty", "actual_qty"],
    ),
    "staffing": (
        preprocess_staffing_row,
        ["date", "store_id", "hour", "sales", "staff_actual", "staff_recommended"],
    ),
}


def normalize_dataset(dataset_type: str, path: str | Path) -> list[dict[str, object]]:
    preprocessor, _ = PREPROCESSORS[dataset_type]
    return [preprocessor(row) for row in load_csv_rows(path)]


def profile_dataset(dataset_type: str, path: str | Path) -> dict[str, object]:
    rows = normalize_dataset(dataset_type, path)
    _, required_fields = PREPROCESSORS[dataset_type]

    profile: dict[str, object] = {
        "dataset_type": dataset_type,
        "row_count": len(rows),
        "missing_fields": missing_fields(rows, required_fields),
    }

    numeric_candidates = [
        key
        for key, value in rows[0].items()
        if rows and isinstance(value, (int, float))
    ] if rows else []

    profile["numeric_profiles"] = {
        key: profile_numeric(rows, key) for key in numeric_candidates
    }
    return profile
