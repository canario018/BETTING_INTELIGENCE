from app.intelligence_center import rank_signals, build_intelligence_center


def rec(key, score, conf, typ="STABLE_MARKET", sure=0, anomaly=False):
    return {
        "calculated_at": "2026-09-04T10:00:00", "signal_key": key, "event_key": key,
        "canonical_sport": "FOOTBALL", "home_team": "A", "away_team": "B",
        "market_type": "MATCH_RESULT", "line": None, "selection_code": "HOME",
        "signal_type": typ, "strength": score, "confidence": conf,
        "surebet_profit_percent": sure, "anomaly": anomaly,
        "evidence": {"freshness_score": 95, "divergence_score": 60, "samples": 30},
    }


def test_surebet_gets_priority():
    rows = rank_signals([rec("a", 60, 70), rec("b", 60, 70, "SUREBET", 2.0)])
    assert rows[0]["signal_key"] == "b"
    assert rows[0]["ranking_priority"] in {"HIGH", "CRITICAL"}


def test_ranking_is_not_probability():
    rows = rank_signals([rec("a", 80, 90)])[0]
    assert 0 <= rows["ranking_score"] <= 100
    assert "probability" not in rows["ranking_reason"].lower()


def test_center_aggregates_sport_market_and_counts():
    payload = build_intelligence_center([rec("a", 80, 90), rec("b", 55, 60, "ANOMALY", anomaly=True)], top_n=2)
    assert payload["total_signals"] == 2
    assert payload["by_sport"][0]["key"] == "FOOTBALL"
    assert payload["by_market"][0]["key"] == "MATCH_RESULT"
    assert payload["top_opportunities"][0]["rank"] == 1
