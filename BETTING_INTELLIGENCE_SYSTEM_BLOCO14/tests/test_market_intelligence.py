from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.database.models import OddSnapshotModel
from app.opportunities.models import SurebetOpportunityModel, SurebetObservationModel, BookmakerRankingModel
from app.opportunities.temporal import movement_series, calculate_bookmaker_ranking, update_lifetimes


def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def add_odd(db, t, book, sel, odd):
    db.add(OddSnapshotModel(
        collected_at=t, bookmaker=book, source_url="x", sport="Futebol", league="L", event_id="1",
        home_team="Alpha FC", away_team="Beta SC", market_name="M", market_type="MATCH_RESULT",
        selection_name=sel, selection_code=sel, line=None, odd=odd, raw_key=f"{book}-{sel}-{t.isoformat()}",
    ))
    db.commit()


def test_movement_series_direction_and_speed():
    db = session()
    t = datetime.utcnow()
    add_odd(db, t, "A", "HOME", 2.0)
    add_odd(db, t + timedelta(minutes=10), "A", "HOME", 2.2)
    data = movement_series(db, type("SB", (), {"market_type":"MATCH_RESULT", "line":None, "home_team":"Alpha FC", "away_team":"Beta SC"})(), 24)
    row = next(x for x in data if x["bookmaker"] == "A")
    assert row["direction"] == "UP"
    assert abs(row["speed_per_minute"] - 0.02) < 1e-9
    assert row["samples"] == 2


def test_bookmaker_ranking_prefers_best_odd():
    db = session()
    t = datetime.utcnow()
    for book, odd in [("A", 2.5), ("B", 2.0), ("C", 1.8)]:
        add_odd(db, t, book, "HOME", odd)
    ranking = calculate_bookmaker_ranking(db, 24)
    assert ranking[0]["bookmaker"] == "A"
    assert ranking[0]["best_odd_count"] == 1


def test_lifetime_expiration():
    db = session()
    now = datetime.utcnow()
    row = SurebetOpportunityModel(
        detected_at=now - timedelta(seconds=1000), opportunity_key="k", event_key="e", home_team="A", away_team="B",
        sport="Futebol", market_type="MATCH_RESULT", probability_sum=.99, profit_percent=1.01,
        reliability_score=80, max_age_seconds=1, timestamp_spread_seconds=1, bookmaker_count=3, min_odd=2,
        bankroll=1000, guaranteed_return=1010, guaranteed_profit=10, status="ACTIVE", legs_json="[]",
        movement_json="[]", alert_level="HIGH", fingerprint="fp", first_seen_at=now-timedelta(seconds=1200),
        last_seen_at=now-timedelta(seconds=1000), lifetime_seconds=200, times_seen=3, peak_profit_percent=1.2,
        trough_profit_percent=.8,
    )
    db.add(row); db.commit()
    assert update_lifetimes(db, set(), now=now, expire_after_seconds=300) == 1
    assert db.query(SurebetOpportunityModel).one().status == "EXPIRED"
