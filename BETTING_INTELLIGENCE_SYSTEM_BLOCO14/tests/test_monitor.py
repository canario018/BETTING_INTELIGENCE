from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base
from app.database.models import OddSnapshotModel
from app.monitor.models import MonitorRunModel, CollectorHealthModel, MarketChangeModel
from app.monitor.engine import detect_changes, persist_changes


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def record(odd=2.0, book="EstrelaBet"):
    return {
        "canonical_event_id":"FOOTBALL|time|cuiaba|202609042230",
        "canonical_market":"MATCH_RESULT", "canonical_selection":"HOME",
        "market_type":"MATCH_RESULT", "selection_code":"HOME", "line":None,
        "bookmaker":book, "odd":odd, "sport":"Futebol", "home_team":"Time",
        "away_team":"Cuiaba", "event_id":"1", "event_start_at":datetime(2026,9,4,22,30),
    }


def add_snapshot(db, odd=2.0):
    db.add(OddSnapshotModel(collected_at=datetime(2026,9,4,12,0), bookmaker="EstrelaBet", source_url="x", sport="Futebol", league="Geral", event_id="1", event_start_at=datetime(2026,9,4,22,30), canonical_event_id="FOOTBALL|time|cuiaba|202609042230", canonical_sport="FOOTBALL", canonical_market="MATCH_RESULT", canonical_selection="HOME", home_team="Time", away_team="Cuiaba", market_name="Vencedor", market_type="MATCH_RESULT", selection_name="Casa", selection_code="HOME", odd=odd, raw_key="x"))
    db.commit()


def test_new_market_change():
    db=make_db(); changes=detect_changes(db,[record()],detected_at=datetime(2026,9,4,12,1))
    assert len(changes)==1 and changes[0]["change_type"]=="NEW"


def test_odd_change_direction_and_percent():
    db=make_db(); add_snapshot(db,2.0)
    changes=detect_changes(db,[record(2.2)],detected_at=datetime(2026,9,4,12,1))
    assert len(changes)==1; assert changes[0]["direction"]=="UP"; assert round(changes[0]["delta_percent"],2)==10.0


def test_threshold_filters_tiny_change():
    db=make_db(); add_snapshot(db,2.0)
    changes=detect_changes(db,[record(2.00001)],threshold_percent=0.01,threshold_absolute=0.001,detected_at=datetime(2026,9,4,12,1))
    assert changes==[]


def test_persist_change():
    db=make_db(); c=detect_changes(db,[record()],detected_at=datetime(2026,9,4,12,1)); assert persist_changes(db,c)==1
    assert db.query(MarketChangeModel).count()==1


def test_monitor_tables_exist():
    db=make_db(); assert db.query(MonitorRunModel).count()==0; assert db.query(CollectorHealthModel).count()==0
