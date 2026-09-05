from __future__ import annotations
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index
from app.database.connection import Base

class MonitorRunModel(Base):
    __tablename__ = "monitor_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, nullable=False, index=True)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, index=True)
    collectors_count = Column(Integer, default=0)
    records_normalized = Column(Integer, default=0)
    snapshots_saved = Column(Integer, default=0)
    changes_detected = Column(Integer, default=0)
    signals_count = Column(Integer, default=0)
    rankings_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    message = Column(Text, nullable=True)

class CollectorHealthModel(Base):
    __tablename__ = "collector_health"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, nullable=True, index=True)
    checked_at = Column(DateTime, nullable=False, index=True)
    bookmaker = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    latency_ms = Column(Float, nullable=True)
    records_count = Column(Integer, default=0)
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)

class MarketChangeModel(Base):
    __tablename__ = "market_changes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    detected_at = Column(DateTime, nullable=False, index=True)
    change_key = Column(String(512), nullable=False, index=True)
    event_key = Column(String(255), nullable=False, index=True)
    canonical_event_id = Column(String(255), nullable=True, index=True)
    bookmaker = Column(String(50), nullable=False, index=True)
    market_type = Column(String(100), nullable=False)
    line = Column(Float, nullable=True)
    selection_code = Column(String(100), nullable=False)
    previous_odd = Column(Float, nullable=True)
    current_odd = Column(Float, nullable=False)
    delta = Column(Float, nullable=False)
    delta_percent = Column(Float, nullable=False)
    direction = Column(String(20), nullable=False)
    change_type = Column(String(30), nullable=False)
    event_start_at = Column(DateTime, nullable=True)
    processed = Column(Boolean, default=False, index=True)
    payload_json = Column(Text, nullable=True)
    __table_args__ = (Index("idx_market_change_key_time", "change_key", "detected_at"),)
