from __future__ import annotations

from sqlalchemy import inspect, text

from app.database.connection import engine, Base
from app.database.models import OddSnapshotModel

# Importa os módulos que registram modelos SQLAlchemy no Base.metadata.
# NÃO importar OpportunityRankingModel de app.intelligence_center:
# o model de persistência fica em app.intelligence_persistence.
from app.monitor import models as monitor_models  # noqa: F401
from app.opportunities import models as opportunity_models  # noqa: F401
from app.opportunities import temporal_persistence  # noqa: F401
from app.signals import models as signal_models  # noqa: F401
from app.alerts import models as alert_models  # noqa: F401
from app.value import models as value_models  # noqa: F401
from app import intelligence_persistence  # noqa: F401

from app.normalization.canonical import (
    canonical_sport,
    canonical_market,
    canonical_selection,
    event_key,
    parse_event_start,
)


MONITOR_COLUMNS = {
    "value_opportunities_count": "INTEGER DEFAULT 0",
}

COLLECTOR_HEALTH_COLUMNS = {
    "http_status": "INTEGER",
    "response_bytes": "INTEGER",
    "unique_events": "INTEGER DEFAULT 0",
    "duplicate_rate_percent": "FLOAT DEFAULT 0",
    "missing_start_percent": "FLOAT DEFAULT 0",
    "supported_market_percent": "FLOAT DEFAULT 0",
    "quality_score": "FLOAT DEFAULT 0",
}

ODDS_COLUMNS = {
    "event_start_at": "DATETIME",
    "canonical_event_id": "VARCHAR(255)",
    "canonical_sport": "VARCHAR(50)",
    "canonical_market": "VARCHAR(100)",
    "canonical_selection": "VARCHAR(100)",
}


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _existing_columns(inspector, table_name: str) -> set[str]:
    if not _table_exists(inspector, table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _add_missing_columns(conn, table_name: str, columns: dict[str, str]) -> None:
    inspector = inspect(conn)
    if not _table_exists(inspector, table_name):
        return

    existing = _existing_columns(inspector, table_name)
    for name, typ in columns.items():
        if name not in existing:
            conn.execute(
                text(f"ALTER TABLE {table_name} ADD COLUMN {name} {typ}")
            )


def ensure_schema():
    """
    Garante o schema completo antes de executar qualquer ALTER TABLE.

    Ordem obrigatória:
      1. importar os módulos que registram os models;
      2. Base.metadata.create_all() para criar tabelas ausentes;
      3. aplicar migrações incrementais somente nas tabelas existentes.
    """
    # PASSO 1: cria TODAS as tabelas ausentes.
    Base.metadata.create_all(bind=engine)

    # PASSO 2: adiciona apenas colunas que ainda não existem.
    with engine.begin() as conn:
        _add_missing_columns(conn, "odds_snapshots", ODDS_COLUMNS)
        _add_missing_columns(conn, "monitor_runs", MONITOR_COLUMNS)
        _add_missing_columns(conn, "collector_health", COLLECTOR_HEALTH_COLUMNS)


def backfill_canonical_fields(db) -> int:
    """Preenche campos canônicos em snapshots antigos que ainda não possuem ID canônico."""
    rows = (
        db.query(OddSnapshotModel)
        .filter(OddSnapshotModel.canonical_event_id.is_(None))
        .all()
    )

    count = 0
    for row in rows:
        row.event_start_at = parse_event_start(row.event_start_at)
        row.canonical_sport = canonical_sport(row.sport)
        row.canonical_market = canonical_market(row.market_type, row.sport)
        row.canonical_selection = canonical_selection(
            row.selection_name,
            row.selection_code,
        )
        row.canonical_event_id = event_key(
            sport=row.sport,
            home_team=row.home_team,
            away_team=row.away_team,
            league=row.league,
            event_start_at=row.event_start_at,
        )
        count += 1

    if count:
        db.commit()

    return count
