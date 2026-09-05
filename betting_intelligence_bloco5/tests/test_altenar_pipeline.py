import json
from pathlib import Path

from app.collectors.altenar import AltenarCouponCollector

ROOT = Path(__file__).resolve().parents[1]


def test_estrelabet_fixture_is_normalized():
    data = json.loads((ROOT / "resposta_bruta_estrelabet.json").read_text(encoding="utf-8"))
    collector = AltenarCouponCollector("EstrelaBet", "estrelabet", "https://www.estrelabet.bet.br/")
    records = collector.normalize_data(data)

    assert len(records) == 104
    first = records[0]
    assert first["bookmaker"] == "EstrelaBet"
    assert first["sport"] == "Futebol"
    assert first["league"] == "CONCACAF Caribbean Cup"
    assert first["home_team"] == "Cavaliers FC"
    assert first["away_team"] == "Portmore United FC"
    assert first["market_type"] == "MATCH_RESULT"
    assert first["selection_code"] == "HOME"
    assert first["odd"] == 2.5


def test_altenar_files_have_same_contract():
    collector = AltenarCouponCollector("Lotogreen", "lotogreen", "https://lotogreen.bet.br/")
    for filename in ["resposta_bruta_lotogreen.json", "resposta_bruta_multibet.json"]:
        data = json.loads((ROOT / filename).read_text(encoding="utf-8"))
        records = collector.normalize_data(data)
        assert len(records) > 0
        assert all(r["bookmaker"] == "Lotogreen" for r in records)
        assert all(r["odd"] > 1 for r in records)
        assert all(r["selection_code"] for r in records)
