from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from itertools import product
from sqlalchemy.orm import Session
from app.database.models import OddSnapshotModel

@dataclass(frozen=True)
class ValueOpportunity:
    opportunity_key: str
    detected_at: datetime
    canonical_event_id: str | None
    bookmaker: str
    sport: str
    home_team: str
    away_team: str
    market_type: str
    selection_code: str
    line: float | None
    odd: float
    implied_probability: float
    fair_probability: float
    fair_odd: float
    edge_percent: float
    expected_value_percent: float
    confidence: float
    source: str = "MARKET_CONSENSUS"

# Only complete mutually-exclusive markets are evaluated by this baseline.
MARKET_UNIVERSE = {
    "MATCH_RESULT": ("HOME", "DRAW", "AWAY"),
    "TOTAL_GOALS": ("OVER", "UNDER"),
    "BOTH_TEAMS_TO_SCORE": ("YES", "NO"),
    "SET_WINNER": ("HOME", "AWAY"),
    "TOTAL_POINTS": ("OVER", "UNDER"),
    "HANDICAP": ("HOME", "AWAY"),
}

def _now(): return datetime.now(timezone.utc).replace(tzinfo=None)

def _event(row):
    return getattr(row, "canonical_event_id", None) or f"{row.sport}|{row.home_team}|{row.away_team}|{row.event_start_at}"

def _market(row): return getattr(row, "canonical_market", None) or row.market_type

def _selection(row): return getattr(row, "canonical_selection", None) or row.selection_code

def _key(row): return (_event(row), _market(row), row.line)

def latest_rows(db: Session, lookback_hours: int = 24, max_age_seconds: int = 300):
    cutoff = _now() - timedelta(hours=lookback_hours)
    rows = db.query(OddSnapshotModel).filter(OddSnapshotModel.collected_at >= cutoff).order_by(OddSnapshotModel.collected_at.desc(), OddSnapshotModel.id.desc()).all()
    now = _now(); latest = {}
    for r in rows:
        age = (now-r.collected_at).total_seconds() if r.collected_at else 999999
        if age > max_age_seconds: continue
        key = (_key(r), r.bookmaker, _selection(r))
        if key not in latest: latest[key] = r
    return list(latest.values())

def _devig(probs: dict[str, float]) -> dict[str, float]:
    total = sum(probs.values())
    return {k: v / total for k, v in probs.items()} if total > 0 else {}

def find_value_opportunities(rows, min_ev_percent: float = 3.0, min_edge_percent: float = 1.0, min_bookmakers: int = 2, max_age_seconds: int = 300):
    groups = defaultdict(list)
    for r in rows:
        market = _market(r); sel = _selection(r)
        if market not in MARKET_UNIVERSE or sel not in MARKET_UNIVERSE[market] or r.odd <= 1: continue
        groups[_key(r)].append(r)
    out = []
    now = _now()
    for key, group in groups.items():
        universe = MARKET_UNIVERSE[_market(group[0])]
        by_sel = defaultdict(list)
        for r in group: by_sel[_selection(r)].append(r)
        if any(not by_sel[s] for s in universe): continue
        if len({r.bookmaker for r in group}) < min_bookmakers: continue
        # Market-consensus baseline: each bookmaker's complete book is de-vigged,
        # then probabilities are averaged. This is NOT an independent prediction model.
        book_probs = []
        for bookmaker in {r.bookmaker for r in group}:
            selected = {}
            for r in group:
                if r.bookmaker == bookmaker: selected[_selection(r)] = max(selected.get(_selection(r), 0), float(r.odd))
            if all(s in selected for s in universe):
                book_probs.append(_devig({s: 1.0/selected[s] for s in universe}))
        if len(book_probs) < min_bookmakers: continue
        fair = {s: sum(p[s] for p in book_probs)/len(book_probs) for s in universe}
        fair = _devig(fair)
        confidence = min(100.0, 45.0 + 8.0*len(book_probs) + 2.0*len({r.bookmaker for r in group}))
        for s in universe:
            best = max(by_sel[s], key=lambda r: r.odd)
            implied = 1.0 / best.odd
            fair_p = fair[s]
            fair_odd = 1.0 / fair_p if fair_p > 0 else 999.0
            edge = (fair_p - implied) * 100.0
            ev = (fair_p * best.odd - 1.0) * 100.0
            age = (now-best.collected_at).total_seconds() if best.collected_at else 999999
            if age > max_age_seconds or edge < min_edge_percent or ev < min_ev_percent: continue
            op_key = f"{key[0]}|{key[1]}|{key[2]}|{s}|{best.bookmaker}"
            out.append(ValueOpportunity(op_key, now, getattr(best,'canonical_event_id',None), best.bookmaker, best.sport, best.home_team, best.away_team, _market(best), s, best.line, best.odd, implied, fair_p, fair_odd, edge, ev, confidence))
    return sorted(out, key=lambda x: (x.expected_value_percent, x.confidence, x.odd), reverse=True)

def analyze_database(db: Session, lookback_hours=24, min_ev_percent=3.0, min_edge_percent=1.0, min_bookmakers=2, max_age_seconds=300):
    return find_value_opportunities(latest_rows(db, lookback_hours, max_age_seconds), min_ev_percent, min_edge_percent, min_bookmakers, max_age_seconds)
