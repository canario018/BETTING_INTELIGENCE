from datetime import datetime, timedelta
from types import SimpleNamespace
from app.opportunities.service import reliability_score, alert_level, fingerprint


def test_score_and_alert_levels():
    sb = SimpleNamespace(profit_percent=2.0, max_age_seconds=1.0, timestamp_spread_seconds=1.0, bookmaker_count=3)
    score = reliability_score(sb)
    assert 0 < score <= 100
    assert alert_level(score, sb.profit_percent) in {"CRITICAL", "HIGH", "MEDIUM"}


def test_fingerprint_changes_with_odd():
    leg = SimpleNamespace(bookmaker="A", selection_code="HOME", odd=2.0)
    sb1 = SimpleNamespace(event_key="e", market_type="MATCH_RESULT", line=None, legs=(leg,))
    leg2 = SimpleNamespace(bookmaker="A", selection_code="HOME", odd=2.1)
    sb2 = SimpleNamespace(event_key="e", market_type="MATCH_RESULT", line=None, legs=(leg2,))
    assert fingerprint(sb1) != fingerprint(sb2)
