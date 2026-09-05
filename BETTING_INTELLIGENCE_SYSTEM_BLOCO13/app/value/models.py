from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from app.database.connection import Base

class ValueOpportunityModel(Base):
    __tablename__ = "value_opportunities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_key = Column(String(255), nullable=False, index=True)
    detected_at = Column(DateTime, nullable=False, index=True)
    canonical_event_id = Column(String(255), nullable=True, index=True)
    bookmaker = Column(String(80), nullable=False, index=True)
    sport = Column(String(50), nullable=False, index=True)
    home_team = Column(String(120), nullable=False)
    away_team = Column(String(120), nullable=False)
    market_type = Column(String(80), nullable=False, index=True)
    selection_code = Column(String(80), nullable=False)
    line = Column(Float, nullable=True)
    odd = Column(Float, nullable=False)
    implied_probability = Column(Float, nullable=False)
    fair_probability = Column(Float, nullable=False)
    fair_odd = Column(Float, nullable=False)
    edge_percent = Column(Float, nullable=False)
    expected_value_percent = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    source = Column(String(50), nullable=False, default="MARKET_CONSENSUS")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    __table_args__ = (Index("idx_value_event_market", "canonical_event_id", "market_type", "line"),)

class ValueObservationModel(Base):
    __tablename__ = "value_observations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_key = Column(String(255), nullable=False, index=True)
    observed_at = Column(DateTime, nullable=False, index=True)
    bookmaker = Column(String(80), nullable=False)
    odd = Column(Float, nullable=False)
    fair_probability = Column(Float, nullable=False)
    fair_odd = Column(Float, nullable=False)
    edge_percent = Column(Float, nullable=False)
    expected_value_percent = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
