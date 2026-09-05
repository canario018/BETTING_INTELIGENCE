from datetime import datetime
from types import SimpleNamespace

from app.analytics.arbitrage import find_surebets


def row(book, code, odd, home="A", away="B", market="MATCH_RESULT", line=None):
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
        collected_at=datetime.now(),
    )


def test_three_way_surebet_with_distinct_books():
    rows = [
        row("A", "HOME", 3.40),
        row("B", "DRAW", 4.20),
        row("C", "AWAY", 3.80),
    ]
    result = find_surebets(rows, min_profit_percent=0.01)
    assert len(result) == 1
    assert result[0].profit_percent > 0
    assert {x.bookmaker for x in result[0].legs} == {"A", "B", "C"}


def test_incomplete_one_x_two_is_not_surebet():
    rows = [row("A", "HOME", 5.0), row("B", "AWAY", 5.0)]
    assert find_surebets(rows, min_profit_percent=0.01) == []


def test_same_bookmaker_is_not_reused():
    rows = [
        row("A", "HOME", 3.0),
        row("A", "DRAW", 5.0),
        row("B", "DRAW", 4.0),
        row("C", "AWAY", 4.0),
    ]
    result = find_surebets(rows, min_profit_percent=0.01)
    assert len(result) == 1
    assert result[0].legs[1].bookmaker == "B"
