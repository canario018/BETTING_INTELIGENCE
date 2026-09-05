from datetime import datetime, timedelta
from types import SimpleNamespace

from app.analytics.arbitrage import best_odds, find_surebets


def row(book, code, odd, collected_at=None, home="A", away="B", market="MATCH_RESULT", line=None):
    return SimpleNamespace(
        bookmaker=book,
        selection_code=code,
        selection_name=code,
        odd=odd,
        home_team=home,
        away_team=away,
        sport="Futebol",
        market_type=market,
        line=line,
        collected_at=collected_at or datetime.now(),
        event_id=f"{home}-{away}",
    )


def test_best_odd_is_selected_per_selection():
    rows = [row("A", "HOME", 3.0), row("B", "HOME", 3.5), row("C", "DRAW", 4.0)]
    result = best_odds(rows)
    key = next(iter(result))
    assert result[key]["HOME"].bookmaker == "B"
    assert result[key]["HOME"].odd == 3.5


def test_timestamp_freshness_rejects_stale_leg():
    now = datetime.now()
    rows = [
        row("A", "HOME", 4.0, now),
        row("B", "DRAW", 4.0, now),
        row("C", "AWAY", 4.0, now - timedelta(minutes=10)),
    ]
    assert find_surebets(rows, min_profit_percent=0.01, max_age_seconds=180) == []


def test_timestamp_spread_rejects_misaligned_snapshot():
    now = datetime.now()
    rows = [
        row("A", "HOME", 4.0, now),
        row("B", "DRAW", 4.0, now),
        row("C", "AWAY", 4.0, now - timedelta(seconds=60)),
    ]
    assert find_surebets(rows, min_profit_percent=0.01, max_age_seconds=180, max_timestamp_spread_seconds=30) == []


def test_conservative_team_normalization_matches_common_suffixes():
    now = datetime.now()
    rows = [
        row("A", "HOME", 3.4, now, home="Cavaliers FC", away="Portmore United FC"),
        row("B", "DRAW", 4.2, now, home="Portmore United FC", away="Cavaliers FC"),
        row("C", "AWAY", 3.8, now, home="Cavaliers FC", away="Portmore United FC"),
    ]
    result = find_surebets(rows, min_profit_percent=0.01)
    assert len(result) == 1


def test_stakes_sum_to_bankroll():
    now = datetime.now()
    rows = [
        row("A", "HOME", 3.4, now),
        row("B", "DRAW", 4.2, now),
        row("C", "AWAY", 3.8, now),
    ]
    result = find_surebets(rows, min_profit_percent=0.01, bankroll=1000)
    stakes = result[0].stakes()
    assert abs(sum(stakes.values()) - 1000) < 1e-8
    assert result[0].guaranteed_profit > 0
