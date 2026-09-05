from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text
from app.database.connection import Base


class MarketSignalModel(Base):
    __tablename__ = "market_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    calculated_at = Column(DateTime, nullable=False, index=True)
    signal_key = Column(String(900), nullable=False, index=True)
    event_key = Column(String(700), nullable=False, index=True)
    canonical_event_id = Column(String(255), nullable=True, index=True)
    canonical_sport = Column(String(50), nullable=True, index=True)
    home_team = Column(String(120), nullable=False)
    away_team = Column(String(120), nullable=False)
    market_type = Column(String(80), nullable=False, index=True)
    line = Column(Float, nullable=True)
    selection_code = Column(String(80), nullable=True, index=True)
    signal_type = Column(String(60), nullable=False, index=True)
    direction = Column(String(30), nullable=False)
    strength = Column(Float, nullable=False, index=True)
    confidence = Column(Float, nullable=False, index=True)
    priority = Column(String(20), nullable=False, index=True)
    current_odd = Column(Float, nullable=True)
    opening_odd = Column(Float, nullable=True)
    delta_percent = Column(Float, nullable=True)
    trend_per_hour = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    latest_zscore = Column(Float, nullable=True)
    anomaly = Column(Boolean, nullable=False, default=False)
    bookmaker_count = Column(Integer, nullable=False, default=0)
    fresh_bookmaker_count = Column(Integer, nullable=False, default=0)
    surebet_profit_percent = Column(Float, nullable=True)
    surebet_score = Column(Float, nullable=True)
    explanation = Column(Text, nullable=False)
    evidence_json = Column(Text, nullable=False, default="{}")
    active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("idx_signal_event_market", "canonical_event_id", "market_type", "line"),
        Index("idx_signal_priority_strength", "priority", "strength"),
        Index("idx_signal_time_type", "calculated_at", "signal_type"),
    )
