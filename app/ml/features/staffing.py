from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StaffingFeatures:
    date: str
    store_id: str
    hour: int
    sales: float
    staff_actual: int
    staff_recommended: int


def staffing_gap(features: StaffingFeatures) -> int:
    return features.staff_recommended - features.staff_actual


def staffing_status(features: StaffingFeatures) -> str:
    gap = staffing_gap(features)
    if gap >= 1:
        return "understaffed"
    if gap <= -1:
        return "overstaffed"
    return "balanced"


def opportunity_cost(features: StaffingFeatures) -> int:
    gap = staffing_gap(features)
    if gap <= 0:
        return 0
    return int((features.sales * 0.08) * gap)
