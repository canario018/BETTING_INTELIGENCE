from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.analytics.arbitrage import Surebet, event_identity, latest_rows
from app.database.models import OddSnapshotModel
from app.opportunities.models import SurebetAlertModel, SurebetOpportunityModel


def _norm(v: str) -> str:
    return " ".join(unicodedata.normalize("NFKD", v or "").encode("ascii", "ignore").decode("ascii").lower().split())


def fingerprint(sb: Surebet) -> str:
    legs = "|".join(f"{x.bookmaker}:{x.selection_code}:{x.odd:.6f}" for x in sb.legs)
    raw = f"{sb.event_key}|{sb.market_type}|{sb.line}|{legs}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def reliability_score(sb: Surebet) -> float:
    # Score operacional, não garantia de lucro: combina margem, frescor,
    # diversidade de casas e estabilidade temporal.
    edge = min(max(sb.profit_percent, 0.0), 10.0) / 10.0 * 40.0
    freshness = max(0.0, 1.0 - min(sb.max_age_seconds, 300.0) / 300.0) * 30.0
    sync = max(0.0, 1.0 - min(sb.timestamp_spread_seconds, 120.0) / 120.0) * 15.0
    books = min(sb.bookmaker_count, 3) / 3.0 * 15.0
    return round(min(100.0, edge + freshness + sync + books), 2)


def alert_level(score: float, profit: float) -> str:
    if score >= 85 and profit >= 1.0:
        return "CRITICAL"
    if score >= 70 and profit >= 0.50:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    return "INFO"


def _movement_for_event(db: Session, sb: Surebet, lookback_hours: int = 24) -> list[dict]:
    # Compara snapshots históricos da mesma família de mercado/evento.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(hours=lookback_hours)
    rows = db.query(OddSnapshotModel).filter(OddSnapshotModel.collected_at >= cutoff).all()
    target = []
    for r in rows:
        if event_identity(r) == tuple(sb.event_key.split("|", 3)):
            target.append(r)
    # O event_key textual perde a estrutura original em versões futuras; usa
    # também equipe/mercado como fallback conservador.
    if not target:
        target = [r for r in rows if _norm(r.home_team) in {_norm(sb.home_team), _norm(sb.away_team)}
                  and _norm(r.away_team) in {_norm(sb.home_team), _norm(sb.away_team)}
                  and r.market_type == sb.market_type and r.line == sb.line]
    by = {}
    for r in target:
        key = (r.bookmaker, r.selection_code)
        current = by.get(key)
        if current is None or r.collected_at > current.collected_at:
            by[key] = r
    result = []
    for r in sorted(by.values(), key=lambda x: (x.collected_at, x.bookmaker, x.selection_code)):
        result.append({"bookmaker": r.bookmaker, "selection_code": r.selection_code,
                       "odd": r.odd, "collected_at": r.collected_at.isoformat() if r.collected_at else None})
    return result


def movement_summary(db: Session, sb: Surebet, lookback_hours: int = 24) -> dict:
    rows = db.query(OddSnapshotModel).filter(
        OddSnapshotModel.market_type == sb.market_type,
        OddSnapshotModel.line == sb.line,
    ).order_by(OddSnapshotModel.collected_at.asc()).all()
    # Match conservador de equipes, independente da ordem.
    teams = {_norm(sb.home_team), _norm(sb.away_team)}
    rows = [r for r in rows if {_norm(r.home_team), _norm(r.away_team)} == teams]
    by = {}
    for r in rows:
        key = (r.bookmaker, r.selection_code)
        by.setdefault(key, []).append(r)
    out = []
    for (book, sel), vals in by.items():
        if not vals:
            continue
        first, last = vals[0], vals[-1]
        delta = last.odd - first.odd
        pct = (delta / first.odd * 100.0) if first.odd else 0.0
        out.append({"bookmaker": book, "selection_code": sel, "opening_odd": first.odd,
                    "latest_odd": last.odd, "delta": round(delta, 6),
                    "delta_percent": round(pct, 4), "samples": len(vals)})
    return out


def persist_opportunities(db: Session, surebets: list[Surebet], lookback_hours: int = 24) -> tuple[int, int]:
    detected_at = datetime.now(timezone.utc).replace(tzinfo=None)
    created = updated = 0
    for sb in surebets:
        score = reliability_score(sb)
        level = alert_level(score, sb.profit_percent)
        fp = fingerprint(sb)
        movement = movement_summary(db, sb, lookback_hours)
        legs = [asdict(x) for x in sb.legs]
        for leg in legs:
            if isinstance(leg.get("collected_at"), datetime):
                leg["collected_at"] = leg["collected_at"].isoformat()
        row = db.query(SurebetOpportunityModel).filter_by(fingerprint=fp).first()
        payload = dict(detected_at=detected_at.isoformat(), event_key=sb.event_key,
                       home_team=sb.home_team, away_team=sb.away_team, market_type=sb.market_type,
                       line=sb.line, probability_sum=sb.probability_sum, profit_percent=sb.profit_percent,
                       reliability_score=score, alert_level=level)
        if row is None:
            row = SurebetOpportunityModel(
                detected_at=detected_at, event_key=sb.event_key, home_team=sb.home_team,
                away_team=sb.away_team, sport="Futebol", market_type=sb.market_type, line=sb.line,
                probability_sum=sb.probability_sum, profit_percent=sb.profit_percent,
                reliability_score=score, max_age_seconds=sb.max_age_seconds,
                timestamp_spread_seconds=sb.timestamp_spread_seconds, bookmaker_count=sb.bookmaker_count,
                min_odd=sb.min_odd, bankroll=sb.bankroll, guaranteed_return=sb.guaranteed_return,
                guaranteed_profit=sb.guaranteed_profit, status="ACTIVE", legs_json=json.dumps(legs, ensure_ascii=False),
                movement_json=json.dumps(movement, ensure_ascii=False), alert_level=level, fingerprint=fp)
            db.add(row); db.flush(); created += 1
            db.add(SurebetAlertModel(created_at=detected_at, opportunity_id=row.id, fingerprint=fp,
                                     level=level, title=f"Surebet {level}: {sb.home_team} x {sb.away_team}",
                                     message=f"ROI {sb.profit_percent:.3f}% | Score {score:.1f}",
                                     payload_json=json.dumps(payload, ensure_ascii=False), delivered=1))
        else:
            row.detected_at = detected_at; row.probability_sum = sb.probability_sum
            row.profit_percent = sb.profit_percent; row.reliability_score = score
            row.max_age_seconds = sb.max_age_seconds; row.timestamp_spread_seconds = sb.timestamp_spread_seconds
            row.bookmaker_count = sb.bookmaker_count; row.min_odd = sb.min_odd
            row.guaranteed_return = sb.guaranteed_return; row.guaranteed_profit = sb.guaranteed_profit
            row.legs_json = json.dumps(legs, ensure_ascii=False); row.movement_json = json.dumps(movement, ensure_ascii=False)
            row.alert_level = level; row.status = "ACTIVE"; updated += 1
    db.commit()
    return created, updated


def expire_old_opportunities(db: Session, max_age_seconds: int = 300) -> int:
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=max_age_seconds)
    rows = db.query(SurebetOpportunityModel).filter(
        SurebetOpportunityModel.status == "ACTIVE",
        SurebetOpportunityModel.detected_at < cutoff,
    ).all()
    for row in rows:
        row.status = "EXPIRED"
    db.commit()
    return len(rows)


def export_dashboard_json(db: Session, path: str, limit: int = 200) -> int:
    rows = db.query(SurebetOpportunityModel).order_by(
        SurebetOpportunityModel.reliability_score.desc(), SurebetOpportunityModel.profit_percent.desc()
    ).limit(limit).all()
    payload = []
    for r in rows:
        payload.append({
            "id": r.id, "detected_at": r.detected_at.isoformat(), "event": f"{r.home_team} x {r.away_team}",
            "home_team": r.home_team, "away_team": r.away_team, "market_type": r.market_type, "line": r.line,
            "roi_percent": r.profit_percent, "probability_sum": r.probability_sum,
            "reliability_score": r.reliability_score, "alert_level": r.alert_level, "status": r.status,
            "max_age_seconds": r.max_age_seconds, "timestamp_spread_seconds": r.timestamp_spread_seconds,
            "bookmaker_count": r.bookmaker_count, "min_odd": r.min_odd,
            "guaranteed_return": r.guaranteed_return, "guaranteed_profit": r.guaranteed_profit,
            "legs": json.loads(r.legs_json), "movement": json.loads(r.movement_json),
        })
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(payload)
