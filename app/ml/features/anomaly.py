from __future__ import annotations

from dataclasses import dataclass
from statistics import median


@dataclass
class AnomalyFeatures:
    event_id: str
    store_id: str
    event_type: str
    amount: float


def median_absolute_deviation(values: list[float]) -> float:
    if not values:
        return 0.0
    center = median(values)
    deviations = [abs(value - center) for value in values]
    return median(deviations)


def robust_z_score(value: float, population: list[float]) -> float:
    if not population:
        return 0.0
    center = median(population)
    mad = median_absolute_deviation(population)
    if mad == 0:
        return 0.0
    return 0.6745 * (value - center) / mad


def anomaly_probability(value: float, population: list[float]) -> float:
    z_score = abs(robust_z_score(value, population))
    probability = min(z_score / 3.5, 1.0)
    return round(probability, 2)


def classify_anomaly(probability: float) -> str:
    if probability >= 0.8:
        return "high"
    if probability >= 0.5:
        return "medium"
    return "low"
