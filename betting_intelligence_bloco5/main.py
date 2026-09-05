from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.config.settings import settings
from app.database.connection import Base, SessionLocal, engine
from app.database.repositories import OddsRepository
from app.collectors.registry import build_collectors
from app.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("MAIN")


def run_collector(collector):
    try:
        raw = collector.fetch_raw_data()
        records = collector.normalize_data(raw)
        return collector.sportsbook_name, raw, records, None
    except Exception as exc:
        logger.exception("Erro no collector %s", collector.sportsbook_name)
        return collector.sportsbook_name, None, [], exc


def save_raw(collector_name: str, raw: dict) -> None:
    if not settings.save_raw_json or raw is None:
        return
    output_dir = Path(settings.raw_data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"{collector_name.lower()}_latest.json"
    filename.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    logger.info("=" * 72)
    logger.info("BETTING INTELLIGENCE SYSTEM - COLETA REAL")
    logger.info("=" * 72)

    Base.metadata.create_all(bind=engine)
    collectors = build_collectors(settings)
    if not collectors:
        logger.warning("Nenhum collector ativo. Verifique COLLECTORS no .env")
        return

    logger.info("Collectors ativos: %s", ", ".join(c.sportsbook_name for c in collectors))

    all_records = []
    with ThreadPoolExecutor(max_workers=len(collectors)) as executor:
        futures = [executor.submit(run_collector, c) for c in collectors]
        for future in as_completed(futures):
            name, raw, records, error = future.result()
            if error is None:
                save_raw(name, raw)
                logger.info("%s: %d odds normalizadas", name, len(records))
                all_records.extend(records)
            else:
                logger.error("%s: falhou - %s", name, error)

    if not all_records:
        logger.warning("Nenhuma odd foi normalizada. O banco não será alterado nesta execução.")
        return

    db = SessionLocal()
    try:
        repo = OddsRepository(db, settings.idempotency_window_seconds)
        saved = 0
        skipped = 0
        for record in all_records:
            if repo.save_snapshot(record):
                saved += 1
            else:
                skipped += 1
    finally:
        db.close()

    logger.info("Total de odds normalizadas: %d", len(all_records))
    logger.info("Novos snapshots salvos: %d", saved)
    logger.info("Duplicados ignorados: %d", skipped)
    logger.info("Banco: %s", settings.database_url)
    logger.info("Coleta real concluída.")


if __name__ == "__main__":
    main()
