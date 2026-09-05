from datetime import datetime
from app.normalization.canonical import canonical_sport, canonical_team, canonical_market, canonical_selection, event_key, market_key
from app.matching.event_matcher import events_match
from app.matching.market_matcher import markets_match

class Obj:
    def __init__(self, **kw): self.__dict__.update(kw)

def test_canonical_sport_and_team():
    assert canonical_sport('Futebol') == 'FOOTBALL'
    assert canonical_sport('soccer') == 'FOOTBALL'
    assert canonical_team('Criciúma FC') == 'criciuma'
    assert canonical_team('Cuiabá SC') == 'cuiaba'

def test_canonical_market_and_selection():
    assert canonical_market('Vencedor do encontro') == 'MATCH_RESULT'
    assert canonical_market('Total de Gols') == 'TOTAL_GOALS'
    assert canonical_selection('Criciúma', 'HOME') == 'HOME'
    assert market_key(market_type='TOTAL_GOALS', line=2.5) == 'TOTAL_GOALS|2.5'

def test_event_key_is_stable_across_case_and_accents():
    a = event_key(sport='Futebol', home_team='Criciúma FC', away_team='Cuiabá', league='Série B', event_start_at='2026-09-04T22:30:00Z')
    b = event_key(sport='soccer', home_team='Criciuma', away_team='Cuiaba SC', league='Serie B', event_start_at='2026-09-04T22:30:00+00:00')
    assert a == b

def test_event_match_rejects_different_start_time():
    a=Obj(sport='Futebol',home_team='A FC',away_team='B',event_start_at=datetime(2026,9,4,20,0))
    b=Obj(sport='Football',home_team='B SC',away_team='A',event_start_at=datetime(2026,9,4,23,0))
    assert not events_match(a,b)

def test_event_match_accepts_team_order_and_minor_clock_difference():
    a=Obj(sport='Futebol',home_team='A FC',away_team='B',event_start_at=datetime(2026,9,4,20,0))
    b=Obj(sport='Football',home_team='B',away_team='A SC',event_start_at=datetime(2026,9,4,20,1))
    assert events_match(a,b)

def test_market_match_normalizes_name_and_line():
    a=Obj(market_type='TOTAL_GOALS',market_name='Total de gols',line=2.5,sport='Futebol')
    b=Obj(market_type='Total de Gols',market_name='Total Goals',line=2.50,sport='soccer')
    assert markets_match(a,b)
