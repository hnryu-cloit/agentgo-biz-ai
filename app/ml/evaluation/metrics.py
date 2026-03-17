from __future__ import annotations


def accuracy(labels: list[str], predictions: list[str]) -> float:
    if not labels or len(labels) != len(predictions):
        return 0.0
    matched = sum(1 for label, prediction in zip(labels, predictions) if label == prediction)
    return round(matched / len(labels), 4)


def precision_at_k(labels: list[int], scores: list[float], k: int) -> float:
    if not labels or not scores or k <= 0 or len(labels) != len(scores):
        return 0.0
    ranked = sorted(zip(labels, scores), key=lambda item: item[1], reverse=True)[:k]
    positives = sum(label for label, _ in ranked)
    return round(positives / len(ranked), 4)
