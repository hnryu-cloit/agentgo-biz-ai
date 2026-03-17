from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from app.ml.features.anomaly import anomaly_probability, classify_anomaly
from app.ml.features.churn import ChurnFeatures, build_churn_score, classify_churn_risk
from app.ml.features.inventory import (
    InventoryFeatures,
    inventory_risk_level,
    loss_amount_estimate,
    reorder_quantity,
)
from app.ml.features.menu import MenuFeatures, classify_menu_action, price_adjustment_band, pricing_signal
from app.ml.features.review import score_review_sentiment
from app.ml.features.sales import SalesRecord, sales_factor_breakdown
from app.ml.features.staffing import StaffingFeatures, opportunity_cost, staffing_gap, staffing_status


@dataclass
class ChurnPrediction:
    customer_id: str
    store_id: str
    churn_score: float
    risk_level: str


@dataclass
class ReviewPrediction:
    review_id: str
    store_id: str
    sentiment: str
    confidence: float


@dataclass
class AnomalyPrediction:
    event_id: str
    store_id: str
    event_type: str
    anomaly_probability: float
    severity: str


@dataclass
class SalesFactorPrediction:
    store_id: str
    dominant_factor: str
    top_factors: list[str]
    revenue_delta_pct: float


@dataclass
class MenuStrategyPrediction:
    menu_id: str
    store_id: str
    action: str
    current_margin_rate: float
    recommended_price_min: int
    recommended_price_max: int
    pricing_signal: str


@dataclass
class StaffingPrediction:
    store_id: str
    hour: int
    status: str
    gap: int
    opportunity_cost: int


@dataclass
class InventoryPrediction:
    store_id: str
    item_id: str
    risk_level: str
    reorder_qty: int
    estimated_loss_amount: int


def predict_churn(csv_path: str | Path) -> list[ChurnPrediction]:
    rows: list[ChurnPrediction] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            features = ChurnFeatures(
                customer_id=row["customer_id"],
                store_id=row["store_id"],
                recency=float(row["recency"]),
                frequency=float(row["frequency"]),
                monetary=float(row["monetary"]),
                last_visit_days=float(row["last_visit_days"]),
                coupon_use_rate=float(row["coupon_use_rate"]),
            )
            score = build_churn_score(features)
            rows.append(
                ChurnPrediction(
                    customer_id=features.customer_id,
                    store_id=features.store_id,
                    churn_score=score,
                    risk_level=classify_churn_risk(score),
                )
            )
    return rows


def predict_review_sentiment(csv_path: str | Path) -> list[ReviewPrediction]:
    rows: list[ReviewPrediction] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            sentiment, confidence = score_review_sentiment(row["review_text"])
            rows.append(
                ReviewPrediction(
                    review_id=row["review_id"],
                    store_id=row["store_id"],
                    sentiment=sentiment,
                    confidence=confidence,
                )
            )
    return rows


def predict_anomalies(csv_path: str | Path) -> list[AnomalyPrediction]:
    raw_rows: list[dict[str, str]] = []
    grouped_amounts: dict[str, list[float]] = {}
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw_rows.append(row)
            grouped_amounts.setdefault(row["event_type"], []).append(float(row["amount"]))

    predictions: list[AnomalyPrediction] = []
    for row in raw_rows:
        amounts = grouped_amounts[row["event_type"]]
        probability = anomaly_probability(float(row["amount"]), amounts)
        predictions.append(
            AnomalyPrediction(
                event_id=row["event_id"],
                store_id=row["store_id"],
                event_type=row["event_type"],
                anomaly_probability=probability,
                severity=classify_anomaly(probability),
            )
        )
    return predictions


def predict_sales_factors(csv_path: str | Path) -> list[SalesFactorPrediction]:
    grouped_records: dict[str, list[SalesRecord]] = {}
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            record = SalesRecord(
                date=row["date"],
                store_id=row["store_id"],
                revenue=float(row["revenue"]),
                orders=float(row["orders"]),
                customers=float(row["customers"]),
                avg_ticket=float(row["avg_ticket"]),
                channel=row["channel"],
                weather=row["weather"],
                promo_flag=int(row["promo_flag"]),
            )
            grouped_records.setdefault(record.store_id, []).append(record)

    predictions: list[SalesFactorPrediction] = []
    for store_id, records in grouped_records.items():
        breakdown = sales_factor_breakdown(records)
        predictions.append(
            SalesFactorPrediction(
                store_id=store_id,
                dominant_factor=breakdown["dominant_factor"],
                top_factors=breakdown["top_factors"],
                revenue_delta_pct=breakdown["revenue_delta_pct"],
            )
        )
    return predictions


def predict_menu_strategy(csv_path: str | Path) -> list[MenuStrategyPrediction]:
    predictions: list[MenuStrategyPrediction] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            features = MenuFeatures(
                menu_id=row["menu_id"],
                store_id=row["store_id"],
                price=int(float(row["price"])),
                cost=float(row["cost"]),
                quantity=float(row["quantity"]),
                margin_rate=float(row["margin_rate"]),
                category=row["category"],
            )
            price_band = price_adjustment_band(features)
            signal = pricing_signal(features)
            predictions.append(
                MenuStrategyPrediction(
                    menu_id=features.menu_id,
                    store_id=features.store_id,
                    action=classify_menu_action(features, signal),
                    current_margin_rate=features.margin_rate,
                    recommended_price_min=price_band[0],
                    recommended_price_max=price_band[1],
                    pricing_signal=signal,
                )
            )
    return predictions


def predict_staffing(csv_path: str | Path) -> list[StaffingPrediction]:
    predictions: list[StaffingPrediction] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            features = StaffingFeatures(
                date=row["date"],
                store_id=row["store_id"],
                hour=int(row["hour"]),
                sales=float(row["sales"]),
                staff_actual=int(row["staff_actual"]),
                staff_recommended=int(row["staff_recommended"]),
            )
            predictions.append(
                StaffingPrediction(
                    store_id=features.store_id,
                    hour=features.hour,
                    status=staffing_status(features),
                    gap=staffing_gap(features),
                    opportunity_cost=opportunity_cost(features),
                )
            )
    return predictions


def predict_inventory(csv_path: str | Path) -> list[InventoryPrediction]:
    predictions: list[InventoryPrediction] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            features = InventoryFeatures(
                month=row["month"],
                store_id=row["store_id"],
                item_id=row["item_id"],
                system_qty=float(row["system_qty"]),
                actual_qty=float(row["actual_qty"]),
                loss_rate=float(row["loss_rate"]),
            )
            predictions.append(
                InventoryPrediction(
                    store_id=features.store_id,
                    item_id=features.item_id,
                    risk_level=inventory_risk_level(features),
                    reorder_qty=reorder_quantity(features),
                    estimated_loss_amount=loss_amount_estimate(features),
                )
            )
    return predictions


def to_dicts(items: list[object]) -> list[dict[str, object]]:
    return [asdict(item) for item in items]
