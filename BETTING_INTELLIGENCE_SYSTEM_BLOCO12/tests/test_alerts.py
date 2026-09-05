from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base
from app.alerts.models import AlertEventModel, AlertDeliveryModel
from app.alerts.engine import persist_alert_candidates, severity_for, format_surebet
from app.analytics.arbitrage import Surebet, ArbitrageLeg

def make_db():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def test_severity():
    assert severity_for("SUREBET", 90, 1.2) == "CRITICAL"
    assert severity_for("MARKET_CHANGE", 75) == "HIGH"

def test_alert_dedup_cooldown():
    session=make_db()
    c={"alert_key":"X","event_key":"E","alert_type":"MARKET_CHANGE","severity":"HIGH","score":80,"title":"X","message":"msg","payload":{}}
    assert len(persist_alert_candidates(session,[c],300)) == 1
    assert len(persist_alert_candidates(session,[c],300)) == 0

def test_alert_tables_exist():
    session=make_db()
    assert session.query(AlertEventModel).count() == 0
    assert session.query(AlertDeliveryModel).count() == 0

def test_surebet_message_contains_legs_and_analytical_notice():
    sb=Surebet(event_key="E",home_team="A",away_team="B",market_type="MATCH_RESULT",line=None,probability_sum=.98,profit_percent=2.04,legs=[ArbitrageLeg(bookmaker="Aposta A",selection_code="HOME",selection_name="Casa",odd=2.1),ArbitrageLeg(bookmaker="Aposta B",selection_code="DRAW",selection_name="Empate",odd=3.1),ArbitrageLeg(bookmaker="Aposta C",selection_code="AWAY",selection_name="Fora",odd=4.2)],bankroll=1000,guaranteed_return=1020,guaranteed_profit=20,max_age_seconds=5,timestamp_spread_seconds=2,bookmaker_count=3,min_odd=2.1)
    text=format_surebet(sb)
    assert "Aposta A" in text and "Aposta B" in text and "Aposta C" in text
    assert "Nenhuma aposta é executada automaticamente" in text
