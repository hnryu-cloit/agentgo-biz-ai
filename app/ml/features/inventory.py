from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InventoryFeatures:
    month: str
    store_id: str
    item_id: str
    system_qty: float
    actual_qty: float
    loss_rate: float


def inventory_risk_level(features: InventoryFeatures) -> str:
    if features.loss_rate >= 0.10:
        return "high"
    if features.loss_rate >= 0.06:
        return "medium"
    return "low"


def reorder_quantity(features: InventoryFeatures) -> int:
    base_gap = max(int(features.system_qty - features.actual_qty), 0)
    safety_stock = int(features.system_qty * 0.1)
    if features.loss_rate >= 0.10:
        return base_gap + safety_stock
    if features.loss_rate >= 0.06:
        return base_gap + int(safety_stock * 0.5)
    return max(base_gap, int(features.system_qty * 0.05))


def loss_amount_estimate(features: InventoryFeatures) -> int:
    return int((features.system_qty - features.actual_qty) * 1000)
