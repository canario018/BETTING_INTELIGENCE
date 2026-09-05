import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from app.database.connection import Base

class OddSnapshotModel(Base):
    __tablename__ = "odds_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collected_at = Column(DateTime, nullable=False, index=True)
    bookmaker = Column(String(50), nullable=False, index=True)
    source_url = Column(String(255), nullable=False)
    sport = Column(String(50), nullable=False)
    league = Column(String(100), nullable=False)
    event_id = Column(String(100), nullable=False, index=True)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    market_name = Column(String(100), nullable=False)
    market_type = Column(String(50), nullable=False)
    selection_name = Column(String(100), nullable=False)
    selection_code = Column(String(50), nullable=False)
    line = Column(Float, nullable=True)
    odd = Column(Float, nullable=False)
    currency = Column(String(10), default="BRL")
    raw_key = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_dedup_check', 'event_id', 'bookmaker', 'market_name', 'selection_code', 'line', 'odd'),
    )
