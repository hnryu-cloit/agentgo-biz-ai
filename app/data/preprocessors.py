from __future__ import annotations

from datetime import datetime


def _require(row: dict[str, str], key: str) -> str:
    value = row.get(key, "").strip()
    if value == "":
        raise ValueError(f"Missing required field: {key}")
    return value


def preprocess_sales_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "date": _require(row, "date"),
        "store_id": _require(row, "store_id"),
        "revenue": float(_require(row, "revenue")),
        "orders": float(_require(row, "orders")),
        "customers": float(_require(row, "customers")),
        "avg_ticket": float(_require(row, "avg_ticket")),
        "channel": _require(row, "channel"),
        "weather": _require(row, "weather"),
        "promo_flag": int(_require(row, "promo_flag")),
        "source_name": _require(row, "source_name"),
        "uploaded_at": datetime.fromisoformat(_require(row, "uploaded_at")),
    }


def preprocess_customer_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "customer_id": _require(row, "customer_id"),
        "store_id": _require(row, "store_id"),
        "recency": float(_require(row, "recency")),
        "frequency": float(_require(row, "frequency")),
        "monetary": float(_require(row, "monetary")),
        "last_visit_days": float(_require(row, "last_visit_days")),
        "coupon_use_rate": float(_require(row, "coupon_use_rate")),
        "churned": int(_require(row, "churned")),
        "source_name": _require(row, "source_name"),
        "uploaded_at": datetime.fromisoformat(_require(row, "uploaded_at")),
    }


def preprocess_review_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "review_id": _require(row, "review_id"),
        "store_id": _require(row, "store_id"),
        "rating": int(_require(row, "rating")),
        "review_text": _require(row, "review_text"),
        "sentiment_label": _require(row, "sentiment_label"),
        "source_name": _require(row, "source_name"),
        "uploaded_at": datetime.fromisoformat(_require(row, "uploaded_at")),
    }


def preprocess_anomaly_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "event_id": _require(row, "event_id"),
        "store_id": _require(row, "store_id"),
        "event_type": _require(row, "event_type"),
        "amount": float(_require(row, "amount")),
        "employee_id": _require(row, "employee_id"),
        "event_time": datetime.fromisoformat(_require(row, "event_time")),
        "is_anomaly": int(_require(row, "is_anomaly")),
        "source_name": _require(row, "source_name"),
        "uploaded_at": datetime.fromisoformat(_require(row, "uploaded_at")),
    }


def preprocess_menu_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "menu_id": _require(row, "menu_id"),
        "store_id": _require(row, "store_id"),
        "price": int(float(_require(row, "price"))),
        "cost": float(_require(row, "cost")),
        "quantity": float(_require(row, "quantity")),
        "margin_rate": float(_require(row, "margin_rate")),
        "category": _require(row, "category"),
        "source_name": _require(row, "source_name"),
        "uploaded_at": datetime.fromisoformat(_require(row, "uploaded_at")),
    }


def preprocess_inventory_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "month": _require(row, "month"),
        "store_id": _require(row, "store_id"),
        "item_id": _require(row, "item_id"),
        "system_qty": float(_require(row, "system_qty")),
        "actual_qty": float(_require(row, "actual_qty")),
        "loss_rate": float(_require(row, "loss_rate")),
        "source_name": _require(row, "source_name"),
        "uploaded_at": datetime.fromisoformat(_require(row, "uploaded_at")),
    }


def preprocess_staffing_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "date": _require(row, "date"),
        "store_id": _require(row, "store_id"),
        "hour": int(_require(row, "hour")),
        "sales": float(_require(row, "sales")),
        "staff_actual": int(_require(row, "staff_actual")),
        "staff_recommended": int(_require(row, "staff_recommended")),
        "source_name": _require(row, "source_name"),
        "uploaded_at": datetime.fromisoformat(_require(row, "uploaded_at")),
    }
