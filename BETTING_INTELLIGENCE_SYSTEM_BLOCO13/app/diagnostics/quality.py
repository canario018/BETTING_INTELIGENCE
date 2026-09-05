from __future__ import annotations

from collections import Counter

SUPPORTED = {
    "MATCH_RESULT", "DOUBLE_CHANCE", "DRAW_NO_BET", "TOTAL_GOALS",
    "BOTH_TEAMS_TO_SCORE", "SET_WINNER", "TOTAL_POINTS", "HANDICAP",
}


def assess_records(records: list[dict]) -> dict:
    total = len(records)
    if not total:
        return {
            "records": 0,
            "unique_events": 0,
            "duplicate_rate_percent": 0.0,
            "missing_start_percent": 0.0,
            "supported_market_percent": 0.0,
            "quality_score": 0.0,
        }

    raw_keys = [str(r.get("raw_key", "")) for r in records]
    unique_keys = len(set(raw_keys))
    duplicate_rate = max(0.0, (total - unique_keys) / total * 100.0)
    unique_events = len({str(r.get("event_id", "")) for r in records})
    missing_start = sum(1 for r in records if not r.get("event_start_at")) / total * 100.0
    supported = sum(1 for r in records if r.get("market_type") in SUPPORTED) / total * 100.0

    score = max(0.0, min(100.0,
        35.0
        + min(30.0, unique_events)
        + max(0.0, 20.0 - duplicate_rate)
        + max(0.0, 10.0 - missing_start / 10.0)
        + supported / 20.0
    ))

    return {
        "records": total,
        "unique_events": unique_events,
        "duplicate_rate_percent": round(duplicate_rate, 3),
        "missing_start_percent": round(missing_start, 3),
        "supported_market_percent": round(supported, 3),
        "quality_score": round(score, 2),
        "market_distribution": dict(Counter(r.get("market_type", "OTHER") for r in records)),
    }
