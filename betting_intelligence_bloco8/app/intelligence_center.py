from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from statistics import mean

from app.signals.engine import build_market_signals


def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def clip(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(v)))


def _norm(v):
    return str(v or "").strip().upper()


def rank_signals(records: list[dict], top_n: int = 100) -> list[dict]:
    """Create a deterministic opportunity ranking from BLOCO 8 evidence.

    This is an analytical prioritization score, not a win probability.
    """
    ranked = []
    for r in records:
        strength = float(r.get("strength") or 0)
        confidence = float(r.get("confidence") or 0)
        surebet = float(r.get("surebet_profit_percent") or 0)
        reliability = float(r.get("reliability_score") or 0)
        freshness = float((r.get("evidence") or {}).get("freshness_score") or 0)
        divergence = float((r.get("evidence") or {}).get("divergence_score") or 0)
        samples = int((r.get("evidence") or {}).get("samples") or 0)
        anomaly = bool(r.get("anomaly"))

        # Reliability is optional in BLOCO 8; when absent, derive a conservative proxy.
        if reliability <= 0:
            reliability = clip(0.55 * confidence + 0.25 * freshness + 0.20 * min(samples / 20, 1) * 100)

        # Surebet edge gets a capped contribution; ROI is not allowed to dominate the score.
        surebet_component = clip(surebet * 20.0)
        temporal_component = clip(0.65 * strength + 0.35 * confidence)
        market_component = clip(0.55 * divergence + 0.45 * freshness)
        anomaly_bonus = 8.0 if anomaly else 0.0

        # Priority score: weighted evidence, with a clear premium for confirmed surebets.
        score = (
            0.34 * temporal_component
            + 0.22 * reliability
            + 0.16 * market_component
            + 0.14 * confidence
            + 0.10 * surebet_component
            + 0.04 * anomaly_bonus
        )
        if _norm(r.get("signal_type")) == "SUREBET":
            score = max(score, clip(70 + surebet_component * 0.35 + 0.25 * reliability))

        rr = dict(r)
        rr["reliability_score"] = round(reliability, 2)
        rr["ranking_score"] = round(clip(score), 2)
        rr["ranking_priority"] = (
            "CRITICAL" if score >= 85 else "HIGH" if score >= 70 else "MEDIUM" if score >= 50 else "LOW"
        )
        rr["ranking_reason"] = _ranking_reason(rr)
        ranked.append(rr)

    ranked.sort(key=lambda x: (x["ranking_score"], x.get("strength", 0), x.get("confidence", 0)), reverse=True)
    for i, r in enumerate(ranked[:top_n], 1):
        r["rank"] = i
    return ranked[:top_n]


def _ranking_reason(r: dict) -> str:
    parts = []
    if r.get("signal_type") == "SUREBET":
        parts.append("surebet confirmada")
    if float(r.get("strength") or 0) >= 70:
        parts.append("sinal forte")
    if float(r.get("confidence") or 0) >= 80:
        parts.append("evidência confiável")
    if float(r.get("reliability_score") or 0) >= 80:
        parts.append("alta confiabilidade")
    if float((r.get("evidence") or {}).get("divergence_score") or 0) >= 45:
        parts.append("divergência entre casas")
    if r.get("anomaly"):
        parts.append("anomalia temporal")
    return "; ".join(parts) if parts else "sinal priorizado pelo conjunto de evidências"


def build_intelligence_center(records: list[dict], *, top_n: int = 50) -> dict:
    ranked = rank_signals(records, top_n=max(top_n, len(records)))
    top = ranked[:top_n]
    by_type = Counter(r.get("signal_type") for r in ranked)
    by_sport = defaultdict(list)
    by_market = defaultdict(list)
    for r in ranked:
        by_sport[r.get("canonical_sport") or "UNKNOWN"].append(r)
        by_market[r.get("market_type") or "UNKNOWN"].append(r)

    def aggregate(groups):
        out = []
        for key, rows in sorted(groups.items(), key=lambda kv: mean(x["ranking_score"] for x in kv[1]), reverse=True):
            out.append({
                "key": key,
                "signals": len(rows),
                "average_ranking_score": round(mean(x["ranking_score"] for x in rows), 2),
                "max_ranking_score": round(max(x["ranking_score"] for x in rows), 2),
                "surebets": sum(1 for x in rows if x.get("signal_type") == "SUREBET"),
                "anomalies": sum(1 for x in rows if x.get("anomaly")),
            })
        return out

    critical = [r for r in ranked if r["ranking_priority"] == "CRITICAL"]
    return {
        "generated_at": utcnow_naive().isoformat(),
        "total_signals": len(records),
        "ranked_signals": len(ranked),
        "critical_count": len(critical),
        "high_count": sum(1 for r in ranked if r["ranking_priority"] == "HIGH"),
        "signal_type_counts": dict(by_type),
        "top_opportunities": top,
        "by_sport": aggregate(by_sport),
        "by_market": aggregate(by_market),
        "analytical_only": True,
    }


def export_intelligence_center(payload: dict, path: str = "data/opportunities/intelligence_center.json") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
