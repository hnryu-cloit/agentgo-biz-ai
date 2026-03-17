from __future__ import annotations


def profile_numeric(rows: list[dict[str, object]], field: str) -> dict[str, float]:
    values = [float(row[field]) for row in rows]
    if not values:
        return {"count": 0, "min": 0.0, "max": 0.0, "mean": 0.0}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": round(sum(values) / len(values), 4),
    }


def missing_fields(rows: list[dict[str, object]], required_fields: list[str]) -> dict[str, int]:
    counts = {field: 0 for field in required_fields}
    for row in rows:
        for field in required_fields:
            if row.get(field) in ("", None):
                counts[field] += 1
    return counts
