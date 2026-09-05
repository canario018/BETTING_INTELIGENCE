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
    event_start_at = Column(DateTime, nullable=True, index=True)
    canonical_event_id = Column(String(255), nullable=True, index=True)
    canonical_sport = Column(String(50), nullable=True, index=True)
    canonical_market = Column(String(100), nullable=True, index=True)
    canonical_selection = Column(String(100), nullable=True, index=True)
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
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None))

    __table_args__ = (
        Index('idx_dedup_check', 'event_id', 'bookmaker', 'market_name', 'selection_code', 'line', 'odd'),
    )

# BLOCO 9 — Opportunity Ranking persistence model registration
from app.intelligence_persistence import OpportunityRankingModel  # noqa: E402,F401
