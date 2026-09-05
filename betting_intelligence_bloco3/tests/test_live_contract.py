import json
from pathlib import Path

from app.collectors.estrelabet import EstrelaBetCollector
from app.collectors.lotogreen import LotogreenCollector
from app.collectors.multibet import MultibetCollector

BASE = Path(__file__).resolve().parents[1]


def test_real_captured_payloads_produce_sqlite_contract_records():
    for cls, filename in [
        (EstrelaBetCollector, "resposta_bruta_estrelabet.json"),
        (LotogreenCollector, "resposta_bruta_lotogreen.json"),
        (MultibetCollector, "resposta_bruta_multibet.json"),
    ]:
        raw = json.loads((BASE / filename).read_text(encoding="utf-8"))
        records = cls().normalize_data(raw)
        assert records
        assert all(r["bookmaker"] for r in records)
        assert all(r["event_id"] for r in records)
        assert all(r["market_type"] for r in records)
        assert all(r["selection_code"] for r in records)
        assert all(r["odd"] > 1 for r in records)
