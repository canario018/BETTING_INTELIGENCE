from __future__ import annotations

import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Index, Text
from app.database.connection import Base


class TemporalMarketStatModel(Base):
    __tablename__ = "temporal_market_stats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    calculated_at = Column(DateTime, nullable=False, index=True)
    window_hours = Column(Integer, nullable=False, index=True)
    event_key = Column(String(700), nullable=False, index=True)
    bookmaker = Column(String(80), nullable=False, index=True)
    selection_code = Column(String(80), nullable=False)
    line = Column(Float, nullable=True)
    market_type = Column(String(80), nullable=False, index=True)
    canonical_event_id = Column(String(255), nullable=True, index=True)
    canonical_sport = Column(String(50), nullable=True, index=True)
    opening_odd = Column(Float, nullable=False)
    latest_odd = Column(Float, nullable=False)
    minimum_odd = Column(Float, nullable=False)
    maximum_odd = Column(Float, nullable=False)
    average_odd = Column(Float, nullable=False)
    median_odd = Column(Float, nullable=False)
    volatility = Column(Float, nullable=False)
    delta = Column(Float, nullable=False)
    delta_percent = Column(Float, nullable=False)
    trend_per_hour = Column(Float, nullable=False)
    average_abs_change = Column(Float, nullable=False)
    latest_zscore = Column(Float, nullable=False)
    anomaly = Column(Boolean, nullable=False, default=False)
    samples = Column(Integer, nullable=False)
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)

    __table_args__ = (Index("idx_temporal_lookup", "window_hours", "event_key", "bookmaker", "selection_code"),)


def persist_temporal_stats(db, records: list[dict]) -> int:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for r in records:
        first = datetime.fromisoformat(r["first_seen"])
        last = datetime.fromisoformat(r["last_seen"])
        db.add(TemporalMarketStatModel(
            calculated_at=now, window_hours=r["window_hours"], event_key=r["event_key"],
            bookmaker=r["bookmaker"], selection_code=r["selection_code"], line=r["line"],
            market_type=r["market_type"], canonical_event_id=r.get("canonical_event_id"),
            canonical_sport=r.get("canonical_sport"), opening_odd=r["opening_odd"], latest_odd=r["latest_odd"],
            minimum_odd=r["minimum_odd"], maximum_odd=r["maximum_odd"], average_odd=r["average_odd"],
            median_odd=r["median_odd"], volatility=r["volatility"], delta=r["delta"],
            delta_percent=r["delta_percent"], trend_per_hour=r["trend_per_hour"],
            average_abs_change=r["average_abs_change"], latest_zscore=r["latest_zscore"],
            anomaly=r["anomaly"], samples=r["samples"], first_seen=first, last_seen=last,
        ))
    db.commit()
    return len(records)


def export_temporal_json(records: list[dict], event_records: list[dict], path: str) -> None:
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({"records": records, "event_summary": event_records}, ensure_ascii=False, indent=2), encoding="utf-8")
