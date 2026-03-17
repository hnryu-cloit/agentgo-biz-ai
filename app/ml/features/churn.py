from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChurnFeatures:
    customer_id: str
    store_id: str
    recency: float
    frequency: float
    monetary: float
    last_visit_days: float
    coupon_use_rate: float


def normalize(value: float, lower: float, upper: float) -> float:
    if upper <= lower:
        return 0.0
    clamped = min(max(value, lower), upper)
    return (clamped - lower) / (upper - lower)


def build_churn_score(features: ChurnFeatures) -> float:
    recency_risk = normalize(features.recency, 0, 60)
    inactivity_risk = normalize(features.last_visit_days, 0, 60)
    frequency_risk = 1 - normalize(features.frequency, 1, 20)
    monetary_risk = 1 - normalize(features.monetary, 10000, 300000)
    coupon_risk = 1 - normalize(features.coupon_use_rate, 0, 0.7)

    score = (
        recency_risk * 0.30
        + inactivity_risk * 0.30
        + frequency_risk * 0.15
        + monetary_risk * 0.15
        + coupon_risk * 0.10
    )
    return round(score * 100, 2)


def classify_churn_risk(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"
