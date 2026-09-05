from __future__ import annotations

import json
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Index
from app.database.connection import Base


class OpportunityRankingModel(Base):
    __tablename__ = "opportunity_rankings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    calculated_at = Column(DateTime, nullable=False, index=True)
    rank = Column(Integer, nullable=False, index=True)
    signal_key = Column(String(700), nullable=False, index=True)
    event_key = Column(String(500), nullable=False, index=True)
    signal_type = Column(String(60), nullable=False, index=True)
    ranking_score = Column(Float, nullable=False, index=True)
    ranking_priority = Column(String(20), nullable=False, index=True)
    strength = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    reliability_score = Column(Float, nullable=False)
    surebet_profit_percent = Column(Float, nullable=True)
    payload_json = Column(Text, nullable=False)
    __table_args__ = (Index("idx_ranking_time_score", "calculated_at", "ranking_score"),)


def persist_ranking(db, ranked: list[dict]) -> int:
    if not ranked:
        return 0
    now = datetime.fromisoformat(ranked[0]["calculated_at"]) if ranked[0].get("calculated_at") else datetime.now(timezone.utc).replace(tzinfo=None)
    for r in ranked:
        db.add(OpportunityRankingModel(
            calculated_at=now, rank=int(r.get("rank", 0)), signal_key=r["signal_key"], event_key=r["event_key"],
            signal_type=r["signal_type"], ranking_score=r["ranking_score"], ranking_priority=r["ranking_priority"],
            strength=r["strength"], confidence=r["confidence"], reliability_score=r["reliability_score"],
            surebet_profit_percent=r.get("surebet_profit_percent"), payload_json=json.dumps(r, ensure_ascii=False),
        ))
    db.commit()
    return len(ranked)
