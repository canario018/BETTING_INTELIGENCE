from sqlalchemy import inspect, text

from app.database.connection import engine
from app.database.models import Base

# Importar os models para que o SQLAlchemy conheça todas as tabelas.
from app.database import models  # noqa: F401

from app.monitor.models import (
    MonitorRunModel,
    CollectorHealthModel,
    MarketChangeModel,
)

from app.alerts.models import (
    AlertEventModel,
    AlertDeliveryModel,
)

from app.value.models import (
    ValueOpportunityModel,
    ValueObservationModel,
)


# Colunas adicionadas ao longo das versões.
MONITOR_COLUMNS = {
    "value_opportunities_count": "INTEGER DEFAULT 0",
}

COLLECTOR_HEALTH_COLUMNS = {
    "http_status": "INTEGER",
    "response_bytes": "INTEGER",
}


def _table_columns(conn, table_name):
    """
    Retorna as colunas existentes de uma tabela SQLite.
    """
    inspector = inspect(conn)

    if table_name not in inspector.get_table_names():
        return set()

    return {
        column["name"]
        for column in inspector.get_columns(table_name)
    }


def _add_missing_columns(conn, table_name, columns):
    """
    Adiciona somente as colunas que ainda não existem.
    """
    existing = _table_columns(conn, table_name)

    for name, typ in columns.items():
        if name not in existing:
            conn.execute(
                text(
                    f"ALTER TABLE {table_name} "
                    f"ADD COLUMN {name} {typ}"
                )
            )


def ensure_schema():
    """
    Garante que o banco esteja criado e atualizado.

    Ordem importante:

    1. create_all()
    2. migrations incrementais
    """

    # ---------------------------------------------------------
    # 1. CRIA TODAS AS TABELAS QUE AINDA NÃO EXISTEM
    # ---------------------------------------------------------
    Base.metadata.create_all(bind=engine)

    # ---------------------------------------------------------
    # 2. MIGRAÇÕES INCREMENTAIS
    # ---------------------------------------------------------
    with engine.begin() as conn:

        # BLOCO 12
        _add_missing_columns(
            conn,
            "monitor_runs",
            MONITOR_COLUMNS,
        )

        _add_missing_columns(
            conn,
            "collector_health",
            COLLECTOR_HEALTH_COLUMNS,
        )
