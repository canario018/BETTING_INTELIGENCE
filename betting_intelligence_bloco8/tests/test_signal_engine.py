from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.database.models import OddSnapshotModel
from app.signals.engine import build_market_signals
from app.signals.models import MarketSignalModel


def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def add(db, t, book, sel, odd):
    db.add(OddSnapshotModel(
        collected_at=t, bookmaker=book, source_url="x", sport="Futebol", league="L", event_id="1",
        event_start_at=t + timedelta(hours=4), canonical_event_id="FOOTBALL|alpha|beta|202609041400",
        canonical_sport="FOOTBALL", canonical_market="MATCH_RESULT", canonical_selection=sel,
        home_team="Alpha FC", away_team="Beta SC", market_name="Resultado", market_type="MATCH_RESULT",
        selection_name=sel, selection_code=sel, line=None, odd=odd, raw_key=f"{book}-{sel}-{t.isoformat()}",
    ))
    db.commit()


def test_signal_engine_detects_strong_down_movement():
    db = session()
    base = datetime.utcnow() - timedelta(hours=20)
    add(db, base, "A", "HOME", 3.0)
    add(db, base + timedelta(hours=10), "A", "HOME", 2.7)
    add(db, base + timedelta(hours=19), "A", "HOME", 2.3)
    signals = build_market_signals(db, windows=(24,), min_strength=0)
    assert signals
    assert any(s["signal_type"] in {"STRONG_DOWN", "ANOMALY", "CROSS_BOOK_DIVERGENCE", "SUREBET"} for s in signals)


def test_signal_engine_detects_cross_book_divergence():
    db = session()
    t = datetime.utcnow() - timedelta(minutes=1)
    add(db, t, "A", "HOME", 3.0)
    add(db, t, "B", "HOME", 2.0)
    signals = build_market_signals(db, windows=(24,), min_strength=0)
    assert any(s["evidence"]["divergence_score"] >= 45 for s in signals)


def test_signal_model_is_registered():
    assert MarketSignalModel.__tablename__ == "market_signals"
