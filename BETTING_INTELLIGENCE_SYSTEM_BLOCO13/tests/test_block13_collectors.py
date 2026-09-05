from datetime import datetime, timezone

from app.collectors.r7bet import R7BetCollector
from app.collectors.betbet import BetBetCollector
from app.collectors.vbet import VBetCollector
from app.collectors.kbet7 import KBet7Collector
from app.collectors.onabet import OnabetCollector


RAW = {
    "events": [{
        "id": 123,
        "participants": [{"name": "Flamengo"}, {"name": "Palmeiras"}],
        "startDate": "2026-09-05T22:00:00Z",
        "leagueName": "Brasileirão",
        "sportName": "Futebol",
        "markets": [{
            "name": "Resultado Final",
            "selections": [
                {"name": "Flamengo", "price": 2.10},
                {"name": "Empate", "price": 3.40},
                {"name": "Palmeiras", "price": 3.20},
            ],
        }, {
            "name": "Total de Gols",
            "selections": [
                {"name": "Mais de 2.5", "price": 1.90},
                {"name": "Menos de 2.5", "price": 1.80},
            ],
        }],
    }]
}


def test_generic_sports_collectors_normalize_core_markets():
    for collector in (R7BetCollector(), BetBetCollector(), VBetCollector(), KBet7Collector()):
        collector.last_collected_at = datetime.now(timezone.utc)
        rows = collector.normalize_data(RAW)
        assert len(rows) == 5
        assert {r["selection_code"] for r in rows[:3]} == {"HOME", "DRAW", "AWAY"}
        assert {r["selection_code"] for r in rows[3:]} == {"OVER", "UNDER"}
        assert all(r["market_type"] in {"MATCH_RESULT", "TOTAL_GOALS"} for r in rows)


def test_onabet_uses_altenar_source():
    c = OnabetCollector()
    assert c.integration == "onabet"
    assert "GetCouponEvents" in c.api_endpoint
