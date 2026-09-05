from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean

from sqlalchemy.orm import Session

from app.analytics.arbitrage import analyze_database
from app.database.models import OddSnapshotModel
from app.opportunities.temporal_engine import WINDOWS_HOURS, build_temporal_intelligence


SIGNAL_TYPES = {
    "SUREBET",
    "STRONG_DOWN",
    "STRONG_UP",
    "ANOMALY",
    "CROSS_BOOK_DIVERGENCE",
    "STABLE_MARKET",
}


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _clip(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _priority(score: float) -> str:
    if score >= 85:
        return "CRITICAL"
    if score >= 70:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    return "LOW"


def _event_market_key(r: dict) -> tuple:
    return (r["event_key"], r["market_type"], r.get("line"))


def _latest_snapshot_map(db: Session, hours: int = 3) -> dict[tuple, list[OddSnapshotModel]]:
    now = utcnow_naive()
    cutoff = now - timedelta(hours=hours)
    rows = db.query(OddSnapshotModel).filter(
        OddSnapshotModel.collected_at >= cutoff,
        OddSnapshotModel.odd > 1,
    ).order_by(OddSnapshotModel.collected_at.desc(), OddSnapshotModel.id.desc()).all()
    out: dict[tuple, list[OddSnapshotModel]] = defaultdict(list)
    seen_books = set()
    for row in rows:
        event_id = getattr(row, "canonical_event_id", None) or f"{row.sport}|{row.home_team}|{row.away_team}|{row.event_start_at}"
        market = getattr(row, "canonical_market", None) or row.market_type
        key = (event_id, market, row.line, row.selection_code)
        if (key, row.bookmaker) in seen_books:
            continue
        seen_books.add((key, row.bookmaker))
        out[key].append(row)
    return out


def _freshness_score(rows: list[OddSnapshotModel], now: datetime) -> float:
    if not rows:
        return 0.0
    ages = [max(0.0, (now - r.collected_at).total_seconds()) for r in rows]
    return _clip(100.0 * (1.0 - min(max(ages), 300.0) / 300.0))


def _divergence_score(rows: list[OddSnapshotModel]) -> float:
    vals = [float(r.odd) for r in rows if r.odd and r.odd > 1]
    if len(vals) < 2:
        return 0.0
    avg = mean(vals)
    if avg <= 0:
        return 0.0
    cv = (max(vals) - min(vals)) / avg
    return _clip(cv * 1000.0)


def _movement_signal(r: dict) -> tuple[str, str, float]:
    delta = float(r.get("delta_percent") or 0.0)
    trend = float(r.get("trend_per_hour") or 0.0)
    vol = float(r.get("volatility") or 0.0)
    z = abs(float(r.get("latest_zscore") or 0.0))
    # A movement is only considered strong when both magnitude and trend support it.
    magnitude = min(abs(delta) / 10.0 * 55.0, 55.0)
    trend_component = min(abs(trend) / 0.10 * 25.0, 25.0)
    anomaly_component = min(z / 3.0 * 20.0, 20.0)
    score = _clip(magnitude + trend_component + anomaly_component)
    if score >= 60 and delta < 0 and trend < 0:
        return "STRONG_DOWN", "DOWN", score
    if score >= 60 and delta > 0 and trend > 0:
        return "STRONG_UP", "UP", score
    if z >= 2.5:
        return "ANOMALY", "DOWN" if delta < 0 else "UP" if delta > 0 else "NEUTRAL", score
    return "", "NEUTRAL", score


def build_market_signals(
    db: Session,
    *,
    windows: tuple[int, ...] = WINDOWS_HOURS,
    min_strength: float = 40.0,
    surebet_lookback_hours: int = 1,
    bankroll: float = 1000.0,
) -> list[dict]:
    """Combines current market state, temporal intelligence and surebet state.

    The output is an analytical signal, not an execution instruction.
    """
    now = utcnow_naive()
    temporal = build_temporal_intelligence(db, windows=windows, now=now)
    latest = _latest_snapshot_map(db, hours=max(3, surebet_lookback_hours * 2))

    # Prefer the richest historical window available for each bookmaker/selection.
    best_temporal: dict[tuple, dict] = {}
    for r in temporal:
        key = (r["event_key"], r["market_type"], r.get("line"), r["bookmaker"], r["selection_code"])
        current = best_temporal.get(key)
        if current is None or r["window_hours"] > current["window_hours"]:
            best_temporal[key] = r

    surebets = analyze_database(
        db,
        lookback_hours=surebet_lookback_hours,
        min_profit_percent=0.0,
        max_age_seconds=180,
        max_timestamp_spread_seconds=30,
        distinct_bookmakers=True,
        bankroll=bankroll,
    )
    surebet_by_market: dict[tuple, object] = {}
    for sb in surebets:
        key = (sb.event_key, sb.market_type, sb.line)
        old = surebet_by_market.get(key)
        if old is None or sb.profit_percent > old.profit_percent:
            surebet_by_market[key] = sb

    records: list[dict] = []
    for key, hist in best_temporal.items():
        event_key, market, line, bookmaker, selection = key
        snapshot_rows = latest.get((hist.get("canonical_event_id") or event_key, market, line, selection), [])
        own_row = next((r for r in snapshot_rows if r.bookmaker == bookmaker), None)
        current_odd = float(own_row.odd) if own_row else float(hist["latest_odd"])
        sb = surebet_by_market.get((event_key, market, line))
        sb_leg = next((leg for leg in sb.legs if leg.bookmaker == bookmaker and leg.selection_code == selection), None) if sb else None

        movement_type, direction, movement_score = _movement_signal(hist)
        divergence = _divergence_score(snapshot_rows)
        freshness = _freshness_score(snapshot_rows, now)
        anomaly = bool(hist.get("anomaly"))

        # Signal strength: temporal movement + cross-book divergence + freshness.
        base = movement_score * 0.55 + divergence * 0.25 + freshness * 0.20
        signal_type = movement_type or ("CROSS_BOOK_DIVERGENCE" if divergence >= 45 else "STABLE_MARKET")
        strength = _clip(base)

        surebet_profit = float(sb.profit_percent) if sb else 0.0
        surebet_score = 0.0
        if sb and sb_leg:
            surebet_score = _clip(50.0 + min(surebet_profit, 5.0) * 10.0 + freshness * 0.25)
            if surebet_profit > 0:
                signal_type = "SUREBET"
                direction = "OPPORTUNITY"
                strength = max(strength, surebet_score)

        confidence = _clip(
            0.45 * freshness
            + 0.25 * min(hist["samples"] / 20.0, 1.0) * 100.0
            + 0.15 * (100.0 if anomaly else 50.0)
            + 0.15 * min(len(snapshot_rows) / 3.0, 1.0) * 100.0
        )
        if signal_type == "STABLE_MARKET":
            strength = max(20.0, strength)
        if strength < min_strength and signal_type not in {"SUREBET", "ANOMALY"}:
            continue

        first = snapshot_rows[0] if snapshot_rows else None
        home = first.home_team if first else hist["home_team"]
        away = first.away_team if first else hist["away_team"]
        canonical_event_id = hist.get("canonical_event_id")
        explanation = (
            f"{signal_type}: odd {current_odd:.4f}; movimento {hist['delta_percent']:.2f}% "
            f"em {hist['window_hours']}h; tendência {hist['trend_per_hour']:.4f}/h; "
            f"volatilidade {hist['volatility']:.4f}; amostras {hist['samples']}"
        )
        if divergence >= 45:
            explanation += f"; divergência entre casas {divergence:.1f}/100"
        if sb:
            explanation += f"; surebet ROI {surebet_profit:.3f}%"

        records.append({
            "calculated_at": now.isoformat(),
            "signal_key": f"{event_key}|{market}|{line}|{selection}",
            "event_key": event_key,
            "canonical_event_id": canonical_event_id,
            "canonical_sport": hist.get("canonical_sport"),
            "home_team": home,
            "away_team": away,
            "market_type": market,
            "line": line,
            "selection_code": selection,
            "bookmaker": bookmaker,
            "signal_type": signal_type,
            "direction": direction,
            "strength": round(strength, 2),
            "confidence": round(confidence, 2),
            "priority": _priority(strength),
            "current_odd": round(current_odd, 6),
            "opening_odd": hist["opening_odd"],
            "delta_percent": hist["delta_percent"],
            "trend_per_hour": hist["trend_per_hour"],
            "volatility": hist["volatility"],
            "latest_zscore": hist["latest_zscore"],
            "anomaly": anomaly,
            "bookmaker_count": len(snapshot_rows),
            "fresh_bookmaker_count": sum(1 for r in snapshot_rows if (now-r.collected_at).total_seconds() <= 180),
            "surebet_profit_percent": round(surebet_profit, 6) if sb else None,
            "surebet_score": round(surebet_score, 2) if sb else None,
            "explanation": explanation,
            "evidence": {
                "window_hours": hist["window_hours"],
                "minimum_odd": hist["minimum_odd"],
                "maximum_odd": hist["maximum_odd"],
                "average_odd": hist["average_odd"],
                "median_odd": hist["median_odd"],
                "average_abs_change": hist["average_abs_change"],
                "divergence_score": round(divergence, 2),
                "freshness_score": round(freshness, 2),
                "samples": hist["samples"],
            },
            "active": True,
        })

    return sorted(records, key=lambda x: (x["strength"], x["confidence"]), reverse=True)
