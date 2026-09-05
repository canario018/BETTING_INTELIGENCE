from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.signals.models import MarketSignalModel


def persist_signals(db, records: list[dict]) -> int:
    now = datetime.fromisoformat(records[0]["calculated_at"]) if records else datetime.utcnow()
    # A run represents a new observation. Keep history instead of overwriting it.
    for r in records:
        db.add(MarketSignalModel(
            calculated_at=now,
            signal_key=r["signal_key"], event_key=r["event_key"], canonical_event_id=r.get("canonical_event_id"),
            canonical_sport=r.get("canonical_sport"), home_team=r["home_team"], away_team=r["away_team"],
            market_type=r["market_type"], line=r.get("line"), selection_code=r.get("selection_code"),
            signal_type=r["signal_type"], direction=r["direction"], strength=r["strength"],
            confidence=r["confidence"], priority=r["priority"], current_odd=r.get("current_odd"),
            opening_odd=r.get("opening_odd"), delta_percent=r.get("delta_percent"), trend_per_hour=r.get("trend_per_hour"),
            volatility=r.get("volatility"), latest_zscore=r.get("latest_zscore"), anomaly=bool(r.get("anomaly")),
            bookmaker_count=r.get("bookmaker_count", 0), fresh_bookmaker_count=r.get("fresh_bookmaker_count", 0),
            surebet_profit_percent=r.get("surebet_profit_percent"), surebet_score=r.get("surebet_score"),
            explanation=r["explanation"], evidence_json=json.dumps(r.get("evidence", {}), ensure_ascii=False), active=True,
        ))
    db.commit()
    return len(records)


def export_signals_json(records: list[dict], path: str = "data/opportunities/market_signals.json") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
