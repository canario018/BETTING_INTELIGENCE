from pathlib import Path

from app.diagnostics.health import save_raw_payload


def test_save_raw_payload_writes_latest_and_metadata(tmp_path: Path):
    raw = {
        "events": [{"id": 123}],
        "markets": [{"id": 10}],
        "odds": [{"id": 20, "price": 2.1}],
    }

    ok, filename, payload_type, digest, top_keys, summary = save_raw_payload(
        raw, tmp_path, "Bet.Bet"
    )

    assert ok is True
    assert filename is not None
    assert Path(filename).name == "bet_bet_latest.json"
    assert Path(filename).exists()
    assert payload_type == "object"
    assert digest and len(digest) == 64
    assert "events" in top_keys
    assert "events[1]" in summary
    assert "markets[1]" in summary
    assert "odds[1]" in summary


def test_save_raw_payload_handles_list_payload(tmp_path: Path):
    raw = [{"id": 1}, {"id": 2}]

    result = save_raw_payload(raw, tmp_path, "R7Bet")

    assert result[0] is True
    assert result[1] is not None
    assert Path(result[1]).name == "r7bet_latest.json"
    assert result[2] == "array"
    assert "array[2]" in result[5]
