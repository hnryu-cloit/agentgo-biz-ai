from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MenuFeatures:
    menu_id: str
    store_id: str
    price: int
    cost: float
    quantity: float
    margin_rate: float
    category: str


def pricing_signal(features: MenuFeatures) -> str:
    if features.margin_rate < 0.32 and features.quantity >= 300:
        return "raise_price"
    if features.margin_rate >= 0.4 and features.quantity < 350:
        return "bundle_or_promote"
    if features.margin_rate < 0.32 and features.quantity < 300:
        return "reformulate_or_review"
    return "maintain"


def price_adjustment_band(features: MenuFeatures) -> tuple[int, int]:
    if features.margin_rate < 0.32:
        return int(features.price * 1.05), int(features.price * 1.12)
    if features.margin_rate >= 0.4 and features.quantity < 350:
        return int(features.price * 0.95), features.price
    return int(features.price * 0.98), int(features.price * 1.03)


def classify_menu_action(features: MenuFeatures, signal: str) -> str:
    if signal == "raise_price":
        return "price_up_test"
    if signal == "bundle_or_promote":
        return "bundle_promotion"
    if signal == "reformulate_or_review":
        return "cost_review"
    return "maintain"
