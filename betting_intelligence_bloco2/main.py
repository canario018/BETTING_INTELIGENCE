from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config.settings import settings
from app.database.connection import Base, SessionLocal, engine
from app.database.repositories import OddsRepository
from app.collectors.registry import build_collectors
from app.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("MAIN")


def run_collector(collector):
    try:
        records = collector.collect()
        return collector.sportsbook_name, records, None
    except Exception as exc:
        logger.exception("Erro no collector %s", collector.sportsbook_name)
        return collector.sportsbook_name, [], exc


def main():
    logger.info("=" * 70)
    logger.info("BETTING INTELLIGENCE SYSTEM - BLOCO 1")
    logger.info("=" * 70)

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
            name, records, error = future.result()
            if error is None:
                logger.info("%s: %d odds normalizadas", name, len(records))
                all_records.extend(records)
            else:
                logger.error("%s: falhou - %s", name, error)

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
    logger.info("Bloco 1 concluído.")


if __name__ == "__main__":
    main()
