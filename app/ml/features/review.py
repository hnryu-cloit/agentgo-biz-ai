from __future__ import annotations

POSITIVE_KEYWORDS = {
    "친절",
    "맛있",
    "빠르",
    "깔끔",
    "좋아요",
    "추천",
    "재방문",
}

NEGATIVE_KEYWORDS = {
    "늦",
    "식었",
    "불친절",
    "별로",
    "누락",
    "아쉽",
    "불편",
    "최악",
}


def score_review_sentiment(text: str) -> tuple[str, float]:
    lowered = text.strip().lower()
    positive_hits = sum(1 for token in POSITIVE_KEYWORDS if token in lowered)
    negative_hits = sum(1 for token in NEGATIVE_KEYWORDS if token in lowered)

    if positive_hits > negative_hits:
        confidence = 0.55 + min(positive_hits * 0.1, 0.35)
        return "positive", round(confidence, 2)
    if negative_hits > positive_hits:
        confidence = 0.55 + min(negative_hits * 0.1, 0.35)
        return "negative", round(confidence, 2)
    return "neutral", 0.55
