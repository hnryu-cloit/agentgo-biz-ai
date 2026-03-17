from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SalesRecord:
    date: str
    store_id: str
    revenue: float
    orders: float
    customers: float
    avg_ticket: float
    channel: str
    weather: str
    promo_flag: int


def pct_change(previous: float, current: float) -> float:
    if previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 2)


def factor_scores_from_deltas(
    customer_delta_pct: float,
    avg_ticket_delta_pct: float,
    channel_delta_pct: float,
    weather_impact_pct: float,
) -> dict[str, float]:
    return {
        "customer_count": abs(customer_delta_pct),
        "avg_ticket": abs(avg_ticket_delta_pct),
        "channel_mix": abs(channel_delta_pct),
        "weather": abs(weather_impact_pct),
    }


def sales_factor_breakdown(records: list[SalesRecord]) -> dict[str, object]:
    if len(records) < 2:
        return {
            "dominant_factor": "insufficient_data",
            "top_factors": ["insufficient_data"],
            "revenue_delta_pct": 0.0,
        }

    midpoint = len(records) // 2
    previous = records[:midpoint]
    current = records[midpoint:]

    prev_revenue = sum(item.revenue for item in previous) / len(previous)
    curr_revenue = sum(item.revenue for item in current) / len(current)
    prev_customers = sum(item.customers for item in previous) / len(previous)
    curr_customers = sum(item.customers for item in current) / len(current)
    prev_avg_ticket = sum(item.avg_ticket for item in previous) / len(previous)
    curr_avg_ticket = sum(item.avg_ticket for item in current) / len(current)

    rainy_previous = sum(1 for item in previous if item.weather == "rain") / len(previous)
    rainy_current = sum(1 for item in current if item.weather == "rain") / len(current)
    promo_previous = sum(item.promo_flag for item in previous) / len(previous)
    promo_current = sum(item.promo_flag for item in current) / len(current)

    factor_scores = {
        "customer_count": abs(pct_change(prev_customers, curr_customers)),
        "avg_ticket": abs(pct_change(prev_avg_ticket, curr_avg_ticket)),
        "weather": abs((rainy_current - rainy_previous) * 100),
        "promotion_mix": abs((promo_current - promo_previous) * 100),
    }
    top_factors = sorted(factor_scores, key=factor_scores.get, reverse=True)[:3]

    return {
        "dominant_factor": top_factors[0],
        "top_factors": top_factors,
        "revenue_delta_pct": pct_change(prev_revenue, curr_revenue),
    }
