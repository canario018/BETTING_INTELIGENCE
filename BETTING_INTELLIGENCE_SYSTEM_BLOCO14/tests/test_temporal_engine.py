from datetime import datetime, timedelta
from types import SimpleNamespace
from app.opportunities.temporal_engine import summarize_series, event_temporal_summary


def row(odd, minute):
    return SimpleNamespace(odd=odd, collected_at=datetime(2026, 9, 4, 10, 0) + timedelta(minutes=minute), id=minute)


def test_summary_metrics():
    s = summarize_series([row(2.0, 0), row(2.2, 30), row(1.8, 60)])
    assert s["opening_odd"] == 2.0
    assert s["latest_odd"] == 1.8
    assert s["minimum_odd"] == 1.8
    assert s["maximum_odd"] == 2.2
    assert s["direction"] == "DOWN"
    assert s["samples"] == 3


def test_anomaly_and_trend_fields_exist():
    vals = [row(2.0, 0), row(2.01, 10), row(2.0, 20), row(2.9, 30)]
    s = summarize_series(vals)
    assert "latest_zscore" in s
    assert "anomaly" in s
    assert "trend_per_hour" in s


def test_event_summary():
    records = [
        {"window_hours": 24, "event_key": "E", "market_type": "MATCH_RESULT", "line": None, "bookmaker": "A", "selection_code": "HOME", "delta_percent": 5, "volatility": .1, "anomaly": True},
        {"window_hours": 24, "event_key": "E", "market_type": "MATCH_RESULT", "line": None, "bookmaker": "B", "selection_code": "HOME", "delta_percent": -3, "volatility": .2, "anomaly": False},
    ]
    out = event_temporal_summary(records)[0]
    assert out["bookmakers"] == 2
    assert out["has_anomaly"] is True
    assert out["max_abs_delta_percent"] == 5
