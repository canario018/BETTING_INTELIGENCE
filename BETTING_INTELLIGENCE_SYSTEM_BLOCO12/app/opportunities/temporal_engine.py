from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean, pstdev

from sqlalchemy.orm import Session

from app.database.models import OddSnapshotModel
from app.analytics.arbitrage import event_identity

WINDOWS_HOURS = (24, 48, 72, 96, 120)


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _key(row: OddSnapshotModel) -> tuple:
    return (event_identity(row), row.bookmaker, row.selection_code, row.line)


def _trend(values: list[tuple[datetime, float]]) -> float:
    if len(values) < 2:
        return 0.0
    x = [(t - values[0][0]).total_seconds() / 3600 for t, _ in values]
    y = [v for _, v in values]
    mx, my = mean(x), mean(y)
    den = sum((a - mx) ** 2 for a in x)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / den if den else 0.0


def _zscore(value: float, values: list[float]) -> float:
    if len(values) < 3:
        return 0.0
    sd = pstdev(values)
    return (value - mean(values)) / sd if sd > 1e-12 else 0.0


def summarize_series(rows: list[OddSnapshotModel]) -> dict:
    rows = sorted(rows, key=lambda r: (r.collected_at, r.id))
    vals = [float(r.odd) for r in rows if r.odd and r.odd > 1]
    if not vals:
        return {}
    opening, latest = vals[0], vals[-1]
    delta = latest - opening
    pct = delta / opening * 100 if opening else 0.0
    changes = [vals[i] - vals[i - 1] for i in range(1, len(vals))]
    trend = _trend([(r.collected_at, float(r.odd)) for r in rows if r.odd and r.odd > 1])
    z = _zscore(latest, vals[:-1]) if len(vals) > 3 else 0.0
    direction = "UP" if delta > 1e-9 else "DOWN" if delta < -1e-9 else "STABLE"
    return {
        "samples": len(vals),
        "opening_odd": round(opening, 6),
        "latest_odd": round(latest, 6),
        "minimum_odd": round(min(vals), 6),
        "maximum_odd": round(max(vals), 6),
        "average_odd": round(mean(vals), 6),
        "median_odd": round(sorted(vals)[len(vals)//2], 6),
        "volatility": round(pstdev(vals), 6) if len(vals) > 1 else 0.0,
        "delta": round(delta, 6),
        "delta_percent": round(pct, 6),
        "direction": direction,
        "trend_per_hour": round(trend, 8),
        "average_abs_change": round(mean(abs(x) for x in changes), 6) if changes else 0.0,
        "latest_zscore": round(z, 4),
        "anomaly": abs(z) >= 2.5,
        "first_seen": rows[0].collected_at.isoformat(),
        "last_seen": rows[-1].collected_at.isoformat(),
    }


def build_temporal_intelligence(db: Session, windows: tuple[int, ...] = WINDOWS_HOURS,
                                 now: datetime | None = None) -> list[dict]:
    now = now or utcnow_naive()
    max_hours = max(windows)
    cutoff = now - timedelta(hours=max_hours)
    rows = db.query(OddSnapshotModel).filter(
        OddSnapshotModel.collected_at >= cutoff,
        OddSnapshotModel.odd > 1,
    ).order_by(OddSnapshotModel.collected_at.asc(), OddSnapshotModel.id.asc()).all()

    output: list[dict] = []
    for window in sorted(set(windows)):
        wcut = now - timedelta(hours=window)
        groups = defaultdict(list)
        for row in rows:
            if row.collected_at >= wcut:
                groups[_key(row)].append(row)
        for key, vals in groups.items():
            event_key, bookmaker, selection, line = key
            summary = summarize_series(vals)
            if not summary:
                continue
            summary.update({
                "window_hours": window,
                "event_key": "|".join(map(str, event_key)) if isinstance(event_key, tuple) else str(event_key),
                "bookmaker": bookmaker,
                "selection_code": selection,
                "line": line,
                "canonical_event_id": getattr(vals[-1], "canonical_event_id", None),
                "canonical_sport": getattr(vals[-1], "canonical_sport", None),
                "canonical_market": getattr(vals[-1], "canonical_market", None),
                "home_team": vals[-1].home_team,
                "away_team": vals[-1].away_team,
                "market_type": vals[-1].market_type,
            })
            output.append(summary)
    return output


def event_temporal_summary(records: list[dict]) -> list[dict]:
    """Aggregates bookmaker/selection records into an event-market intelligence view."""
    grouped = defaultdict(list)
    for r in records:
        grouped[(r["window_hours"], r["event_key"], r["market_type"], r["line"])].append(r)
    out = []
    for (window, event_key, market, line), vals in grouped.items():
        deltas = [v["delta_percent"] for v in vals]
        vol = [v["volatility"] for v in vals]
        anomalies = sum(bool(v["anomaly"]) for v in vals)
        out.append({
            "window_hours": window,
            "event_key": event_key,
            "market_type": market,
            "line": line,
            "bookmakers": len({v["bookmaker"] for v in vals}),
            "selections": len({v["selection_code"] for v in vals}),
            "average_delta_percent": round(mean(deltas), 6) if deltas else 0.0,
            "max_abs_delta_percent": round(max((abs(x) for x in deltas), default=0.0), 6),
            "average_volatility": round(mean(vol), 6) if vol else 0.0,
            "anomaly_count": anomalies,
            "has_anomaly": anomalies > 0,
        })
    return sorted(out, key=lambda x: (x["window_hours"], x["max_abs_delta_percent"]), reverse=True)
