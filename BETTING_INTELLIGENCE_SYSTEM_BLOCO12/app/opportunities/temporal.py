from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.analytics.arbitrage import event_identity
from app.database.models import OddSnapshotModel
from app.opportunities.models import BookmakerRankingModel, SurebetOpportunityModel


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _event_match_key(row):
    return "|".join(map(str, event_identity(row)))


def movement_series(db: Session, sb, lookback_hours: int = 24) -> list[dict]:
    cutoff = utcnow_naive() - timedelta(hours=lookback_hours)
    rows = (
        db.query(OddSnapshotModel)
        .filter(OddSnapshotModel.collected_at >= cutoff,
                OddSnapshotModel.market_type == sb.market_type,
                OddSnapshotModel.line == sb.line)
        .order_by(OddSnapshotModel.collected_at.asc(), OddSnapshotModel.id.asc())
        .all()
    )
    target = getattr(sb, "event_key", None)
    if target:
        rows = [r for r in rows if _event_match_key(r) == target]
    else:
        target_teams = {str(sb.home_team).strip().lower(), str(sb.away_team).strip().lower()}
        rows = [r for r in rows if {str(r.home_team).strip().lower(), str(r.away_team).strip().lower()} == target_teams]
    by = defaultdict(list)
    for r in rows:
        by[(r.bookmaker, r.selection_code)].append(r)

    result = []
    for (bookmaker, selection), vals in sorted(by.items()):
        if not vals:
            continue
        first, last = vals[0], vals[-1]
        delta = last.odd - first.odd
        pct = delta / first.odd * 100 if first.odd else 0.0
        elapsed = max((last.collected_at - first.collected_at).total_seconds(), 0.0)
        speed = delta / (elapsed / 60.0) if elapsed > 0 else 0.0
        direction = "UP" if delta > 0.000001 else "DOWN" if delta < -0.000001 else "STABLE"
        mean = sum(v.odd for v in vals) / len(vals)
        variance = sum((v.odd - mean) ** 2 for v in vals) / len(vals)
        result.append({
            "bookmaker": bookmaker,
            "selection_code": selection,
            "opening_odd": first.odd,
            "latest_odd": last.odd,
            "delta": round(delta, 6),
            "delta_percent": round(pct, 4),
            "direction": direction,
            "speed_per_minute": round(speed, 6),
            "volatility": round(math.sqrt(variance), 6),
            "samples": len(vals),
            "first_seen": first.collected_at.isoformat(),
            "last_seen": last.collected_at.isoformat(),
        })
    return result


def update_lifetimes(db: Session, current_keys: set[str], now: datetime | None = None,
                     expire_after_seconds: int = 300) -> int:
    now = now or utcnow_naive()
    rows = db.query(SurebetOpportunityModel).filter(SurebetOpportunityModel.status == "ACTIVE").all()
    expired = 0
    for row in rows:
        if row.opportunity_key in current_keys:
            continue
        last = row.last_seen_at or row.detected_at
        if (now - last).total_seconds() > expire_after_seconds:
            row.status = "EXPIRED"
            row.lifetime_seconds = max(0.0, (last - (row.first_seen_at or last)).total_seconds())
            expired += 1
    db.commit()
    return expired


def calculate_bookmaker_ranking(db: Session, lookback_hours: int = 24) -> list[dict]:
    cutoff = utcnow_naive() - timedelta(hours=lookback_hours)
    rows = db.query(OddSnapshotModel).filter(OddSnapshotModel.collected_at >= cutoff, OddSnapshotModel.odd > 1).all()
    by_book = defaultdict(list)
    for r in rows:
        by_book[r.bookmaker].append(r)

    # Melhor odd por evento/mercado/linha/seleção.
    best = defaultdict(float)
    for r in rows:
        key = (event_identity(r), r.selection_code)
        best[key] = max(best[key], r.odd)
    best_count = defaultdict(int)
    for r in rows:
        if abs(r.odd - best[(event_identity(r), r.selection_code)]) < 1e-9:
            best_count[r.bookmaker] += 1

    surebet_legs = defaultdict(int)
    surebet_total = 0
    active = db.query(SurebetOpportunityModel).filter(
        SurebetOpportunityModel.detected_at >= cutoff,
        SurebetOpportunityModel.status.in_(["ACTIVE", "EXPIRED"]),
    ).all()
    import json
    for op in active:
        try:
            legs = json.loads(op.legs_json)
        except Exception:
            legs = []
        for leg in legs:
            surebet_legs[leg.get("bookmaker")] += 1
            surebet_total += 1

    out = []
    calculated_at = utcnow_naive()
    for bookmaker, vals in by_book.items():
        snapshots = len(vals)
        markets = len({(event_identity(v), v.selection_code) for v in vals})
        best_rate = best_count[bookmaker] / markets * 100 if markets else 0.0
        leg_rate = surebet_legs[bookmaker] / surebet_total * 100 if surebet_total else 0.0
        avg_odd = sum(v.odd for v in vals) / snapshots if snapshots else 0.0
        score = min(100.0, best_rate * 0.65 + leg_rate * 0.35)
        out.append({
            "bookmaker": bookmaker,
            "snapshots": snapshots,
            "markets_seen": markets,
            "best_odd_count": best_count[bookmaker],
            "best_odd_rate": round(best_rate, 2),
            "surebet_leg_count": surebet_legs[bookmaker],
            "surebet_leg_rate": round(leg_rate, 2),
            "avg_odd": round(avg_odd, 4),
            "ranking_score": round(score, 2),
        })
    return sorted(out, key=lambda x: (x["ranking_score"], x["best_odd_count"]), reverse=True)


def persist_bookmaker_ranking(db: Session, ranking: list[dict]) -> None:
    now = utcnow_naive()
    for item in ranking:
        db.add(BookmakerRankingModel(calculated_at=now, **item))
    db.commit()
