from datetime import datetime, timezone
from types import SimpleNamespace
from app.market_mapping import build_market_matrix, cross_book_opportunities
from app.collectors.r7bet import R7BetCollector


def test_r7_specific_parser():
    raw={"Events":[{"_id":"1","EventName":"Time A vs Time B","SportId":"1","SportName":"Futebol","LeagueName":"Liga","StartEventDate":"2026-09-05T19:00:00Z","Participants":[{"Name":"Time A","VenueRole":"Home"},{"Name":"Time B","VenueRole":"Away"}],"Markets":[{"Name":"Resultado Final","MarketType":{"_id":"ML0","Name":"Resultado Final"},"Selections":[{"selectionName":"Time A","odds":"2.10"},{"selectionName":"Empate","odds":"3.40"},{"selectionName":"Time B","odds":"3.20"}]},{"Name":"Total de Gols Mais/Menos","MarketType":{"_id":"OU0","Name":"Total de Gols Mais/Menos"},"Selections":[{"selectionName":"Mais de 2.5","odds":"1.90"},{"selectionName":"Menos de 2.5","odds":"1.80"}]}] } ]}
    c=R7BetCollector(); c.last_collected_at=datetime.now(timezone.utc)
    rows=c.normalize_data(raw)
    assert len(rows)==5
    assert {r['selection_code'] for r in rows[:3]}=={'HOME','DRAW','AWAY'}
    assert {r['line'] for r in rows[3:]}=={2.5}


def test_matrix_and_surebet():
    now=datetime.now(timezone.utc).replace(tzinfo=None)
    rows=[]
    for book, odds in [('A',(2.2,3.6,3.6)),('B',(2.1,3.7,3.7))]:
        for sel,odd in zip(('HOME','DRAW','AWAY'),odds):
            rows.append(SimpleNamespace(canonical_event_id='E',sport='FOOTBALL',home_team='A',away_team='B',event_start_at=now,canonical_market='MATCH_RESULT',market_type='MATCH_RESULT',canonical_selection=sel,selection_code=sel,selection_name=sel,line=None,bookmaker=book,odd=odd,collected_at=now))
    m=build_market_matrix(rows,max_age_seconds=900)
    assert len(m)==1 and m[0].complete and m[0].bookmakers==2
    o=cross_book_opportunities(m)
    assert o[0]['is_surebet']
