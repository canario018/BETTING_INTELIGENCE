from datetime import datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base
from app.database.models import OddSnapshotModel
from app.database.repositories import OddsRepository


def test_normalized_record_is_persisted():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    repo = OddsRepository(db, idempotency_window_seconds=60)
    record = {
        "collected_at": datetime.now(timezone.utc),
        "bookmaker": "EstrelaBet", "source_url": "https://example.test",
        "sport": "Futebol", "league": "Teste", "event_id": "1",
        "home_team": "Home", "away_team": "Away",
        "market_name": "Vencedor do encontro", "market_type": "MATCH_RESULT",
        "selection_name": "Home", "selection_code": "HOME",
        "line": None, "odd": 2.5, "currency": "BRL", "raw_key": "test-key"
    }
    assert repo.save_snapshot(record) is True
    assert repo.save_snapshot(record) is False
    rows = db.execute(select(OddSnapshotModel)).scalars().all()
    assert len(rows) == 1
    assert rows[0].selection_code == "HOME"
    db.close()
