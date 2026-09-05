from __future__ import annotations
import argparse
from pathlib import Path
from app.database.connection import Base, SessionLocal, engine
from app.database.migrations import ensure_schema, backfill_canonical_fields
from app.opportunities.temporal_engine import WINDOWS_HOURS, build_temporal_intelligence, event_temporal_summary
from app.opportunities.temporal_persistence import persist_temporal_stats, export_temporal_json


def main():
    parser = argparse.ArgumentParser(description="BLOCO 7 — Temporal Intelligence Engine")
    parser.add_argument("--hours", type=int, default=120, help="Janela máxima histórica em horas")
    parser.add_argument("--windows", nargs="+", type=int, default=list(WINDOWS_HOURS), help="Janelas a calcular")
    args = parser.parse_args()
    ensure_schema()
    db = SessionLocal()
    try:
        backfill_canonical_fields(db)
        windows = tuple(w for w in args.windows if 1 <= w <= args.hours)
        records = build_temporal_intelligence(db, windows=windows)
        events = event_temporal_summary(records)
        Base.metadata.create_all(bind=engine)
        persisted = persist_temporal_stats(db, records)
        export_temporal_json(records, events, "data/opportunities/temporal_intelligence.json")
        print("=" * 110)
        print("BETTING INTELLIGENCE — BLOCO 7 / TEMPORAL INTELLIGENCE ENGINE")
        print("=" * 110)
        print(f"Janelas: {', '.join(map(str, windows))}h | séries: {len(records)} | eventos/mercados: {len(events)}")
        print(f"Persistidos: {persisted}")
        print("Métricas: mínimo, máximo, média, mediana, volatilidade, delta, tendência, velocidade de mudança, z-score e anomalia.")
        print("Dataset: data/opportunities/temporal_intelligence.json")
    finally:
        db.close()

if __name__ == "__main__":
    main()
