from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Iterable

from app.normalization.canonical import canonical_market, canonical_selection, canonical_sport, event_key, normalize_line

@dataclass
class MarketCell:
    bookmaker: str
    selection: str
    odd: float
    collected_at: str

@dataclass
class MarketMatrixRow:
    canonical_event_id: str
    sport: str
    home_team: str
    away_team: str
    event_start_at: str | None
    market: str
    line: str
    bookmakers: int
    selections: dict[str, dict]
    complete: bool
    best_selection: str | None
    best_odd: float | None
    best_bookmaker: str | None


CORE_UNIVERSES = {
    "MATCH_RESULT": {"HOME", "DRAW", "AWAY"},
    "TOTAL_GOALS": {"OVER", "UNDER"},
    "BOTH_TEAMS_TO_SCORE": {"YES", "NO"},
    "FIRST_HALF_RESULT": {"HOME", "DRAW", "AWAY"},
    "HANDICAP": {"HOME", "AWAY"},
    "TOTAL_POINTS": {"OVER", "UNDER"},
    "SET_WINNER": {"HOME", "AWAY"},
}


def _latest(rows: Iterable, max_age_seconds: int = 900):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    out = {}
    for r in rows:
        collected = getattr(r, "collected_at", None)
        if not collected: continue
        age = (now - collected).total_seconds()
        if age < 0 or age > max_age_seconds: continue
        event = getattr(r, "canonical_event_id", None) or event_key(
            sport=r.sport, home_team=r.home_team, away_team=r.away_team, event_start_at=r.event_start_at
        )
        market = canonical_market(getattr(r, "canonical_market", None) or r.market_type, r.sport)
        selection = canonical_selection(getattr(r, "canonical_selection", None) or r.selection_name, r.selection_code)
        line = normalize_line(r.line)
        key = (event, market, line, r.bookmaker, selection)
        if key not in out or collected > out[key].collected_at:
            out[key] = r
    return list(out.values())


def build_market_matrix(rows: Iterable, max_age_seconds: int = 900, markets: set[str] | None = None):
    groups = defaultdict(list)
    for r in _latest(rows, max_age_seconds):
        market = canonical_market(getattr(r, "canonical_market", None) or r.market_type, r.sport)
        if markets and market not in markets: continue
        event = getattr(r, "canonical_event_id", None) or event_key(sport=r.sport, home_team=r.home_team, away_team=r.away_team, event_start_at=r.event_start_at)
        groups[(event, market, normalize_line(r.line))].append(r)

    result = []
    for (event, market, line), items in groups.items():
        universe = CORE_UNIVERSES.get(market)
        by_selection = defaultdict(list)
        bookmakers = set()
        for r in items:
            sel = canonical_selection(getattr(r, "canonical_selection", None) or r.selection_name, r.selection_code)
            by_selection[sel].append(r); bookmakers.add(r.bookmaker)
        selection_map = {}
        for sel, vals in by_selection.items():
            best = max(vals, key=lambda x: x.odd)
            selection_map[sel] = {
                "best_odd": best.odd,
                "best_bookmaker": best.bookmaker,
                "bookmakers": sorted({x.bookmaker for x in vals}),
                "count": len(vals),
            }
        complete = bool(universe and universe.issubset(by_selection))
        best_sel = best_odd = best_book = None
        if selection_map:
            best_sel, data = max(selection_map.items(), key=lambda kv: kv[1]["best_odd"])
            best_odd, best_book = data["best_odd"], data["best_bookmaker"]
        first = items[0]
        result.append(MarketMatrixRow(event, canonical_sport(first.sport), first.home_team, first.away_team,
            first.event_start_at.isoformat() if first.event_start_at else None, market, line, len(bookmakers), dict(selection_map), complete,
            best_sel, best_odd, best_book))
    return sorted(result, key=lambda x: (x.event_start_at or "", x.home_team, x.market, x.line))


def cross_book_opportunities(matrix: list[MarketMatrixRow], min_bookmakers: int = 2):
    out = []
    for row in matrix:
        if not row.complete or row.bookmakers < min_bookmakers: continue
        universe = CORE_UNIVERSES[row.market]
        if not universe.issubset(row.selections): continue
        inverse_sum = sum(1.0 / row.selections[s]["best_odd"] for s in universe)
        roi = (1.0 / inverse_sum - 1.0) * 100.0
        divergence = []
        for s in sorted(universe):
            odds = row.selections[s]["best_odd"]
            divergence.append({"selection": s, "best_odd": odds, "bookmaker": row.selections[s]["best_bookmaker"]})
        out.append({"event": row.canonical_event_id, "home": row.home_team, "away": row.away_team, "market": row.market,
                    "line": row.line, "bookmakers": row.bookmakers, "probability_sum": inverse_sum,
                    "arbitrage_roi_percent": roi, "is_surebet": inverse_sum < 1.0, "legs": divergence})
    return sorted(out, key=lambda x: x["arbitrage_roi_percent"], reverse=True)
