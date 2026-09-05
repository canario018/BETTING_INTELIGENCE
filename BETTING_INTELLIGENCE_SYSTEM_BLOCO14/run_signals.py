from __future__ import annotations

import argparse
from app.database.connection import Base, SessionLocal, engine
from app.database.migrations import ensure_schema, backfill_canonical_fields
from app.signals.engine import build_market_signals
from app.signals.persistence import persist_signals, export_signals_json


def main():
    parser = argparse.ArgumentParser(description="BLOCO 8 — Market Intelligence + Signal Engine")
    parser.add_argument("--hours", type=int, default=120, help="Janela temporal máxima")
    parser.add_argument("--windows", nargs="+", type=int, default=[24,48,72,96,120])
    parser.add_argument("--min-strength", type=float, default=40.0)
    parser.add_argument("--surebet-lookback-hours", type=int, default=1)
    parser.add_argument("--bankroll", type=float, default=1000.0)
    parser.add_argument("--output", default="data/opportunities/market_signals.json")
    args = parser.parse_args()
    ensure_schema()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        backfill_canonical_fields(db)
        windows = tuple(sorted(set(w for w in args.windows if 1 <= w <= args.hours)))
        records = build_market_signals(db, windows=windows, min_strength=args.min_strength,
                                       surebet_lookback_hours=args.surebet_lookback_hours,
                                       bankroll=args.bankroll)
        persisted = persist_signals(db, records)
        export_signals_json(records, args.output)
        counts = {}
        for r in records:
            counts[r["signal_type"]] = counts.get(r["signal_type"], 0) + 1
        print("=" * 110)
        print("BETTING INTELLIGENCE — BLOCO 8 / MARKET INTELLIGENCE + SIGNAL ENGINE")
        print("=" * 110)
        print(f"Janelas: {', '.join(map(str, windows))}h | sinais: {len(records)} | persistidos: {persisted}")
        print("Tipos: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        print(f"Saída: {args.output}")
        print("Modo: analítico; nenhum clique, login ou execução de aposta é realizado.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
