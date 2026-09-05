from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.collectors.estrelabet import EstrelaBetCollector
from app.collectors.lotogreen import LotogreenCollector
from app.collectors.multibet import MultibetCollector
from app.config.settings import settings
from app.database.connection import Base, SessionLocal, engine
from app.database.repositories import OddsRepository

COLLECTORS = {
    "estrelabet": (EstrelaBetCollector, "resposta_bruta_estrelabet.json"),
    "lotogreen": (LotogreenCollector, "resposta_bruta_lotogreen.json"),
    "multibet": (MultibetCollector, "resposta_bruta_multibet.json"),
}


def main():
    parser = argparse.ArgumentParser(description="Carrega JSONs capturados para o SQLite")
    parser.add_argument("--input-dir", default=".")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        repo = OddsRepository(db, settings.idempotency_window_seconds)
        total = saved = skipped = 0
        for name, (cls, filename) in COLLECTORS.items():
            path = input_dir / filename
            if not path.exists():
                print(f"{name}: arquivo não encontrado: {path}")
                continue
            raw = json.loads(path.read_text(encoding="utf-8"))
            records = cls().normalize_data(raw)
            local_saved = 0
            for record in records:
                total += 1
                if repo.save_snapshot(record):
                    saved += 1
                    local_saved += 1
                else:
                    skipped += 1
            print(f"{name}: {len(records)} normalizadas | {local_saved} novas")
        print(f"TOTAL: {total} normalizadas | {saved} novas | {skipped} ignoradas")
        print(f"SQLite: {settings.database_url}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
