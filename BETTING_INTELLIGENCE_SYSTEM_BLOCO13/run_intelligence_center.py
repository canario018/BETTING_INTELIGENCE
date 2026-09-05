from __future__ import annotations
import argparse
from app.database.connection import Base, SessionLocal, engine
from app.database.migrations import ensure_schema, backfill_canonical_fields
from app.signals.engine import build_market_signals
from app.intelligence_center import build_intelligence_center, rank_signals, export_intelligence_center
from app.intelligence_persistence import persist_ranking


def main():
    p = argparse.ArgumentParser(description="BLOCO 9 — Opportunity Ranking + Intelligence Center")
    p.add_argument("--hours", type=int, default=120)
    p.add_argument("--windows", nargs="+", type=int, default=[24,48,72,96,120])
    p.add_argument("--min-strength", type=float, default=40.0)
    p.add_argument("--surebet-lookback-hours", type=int, default=1)
    p.add_argument("--bankroll", type=float, default=1000.0)
    p.add_argument("--top", type=int, default=50)
    p.add_argument("--output", default="data/opportunities/intelligence_center.json")
    args = p.parse_args()
    ensure_schema(); Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        backfill_canonical_fields(db)
        windows = tuple(sorted(set(w for w in args.windows if 1 <= w <= args.hours)))
        signals = build_market_signals(db, windows=windows, min_strength=args.min_strength,
            surebet_lookback_hours=args.surebet_lookback_hours, bankroll=args.bankroll)
        ranked = rank_signals(signals, top_n=max(args.top, len(signals)))
        for i, r in enumerate(ranked, 1): r["rank"] = i
        payload = build_intelligence_center(signals, top_n=args.top)
        persisted = persist_ranking(db, ranked)
        export_intelligence_center(payload, args.output)
        print("=" * 110)
        print("BETTING INTELLIGENCE — BLOCO 9 / OPPORTUNITY RANKING + INTELLIGENCE CENTER")
        print("=" * 110)
        print(f"Janelas: {', '.join(map(str, windows))}h | sinais: {len(signals)} | ranking: {len(ranked)} | persistidos: {persisted}")
        print(f"CRITICAL={payload['critical_count']} | HIGH={payload['high_count']}")
        print("Top 10:")
        for r in payload["top_opportunities"][:10]:
            print(f"#{r.get('rank', '?')} {r['ranking_score']:.2f} {r['ranking_priority']:<8} {r['signal_type']:<24} {r['home_team']} x {r['away_team']}")
        print(f"Saída: {args.output}")
        print("Modo: analítico; nenhum clique, login ou execução de aposta é realizado.")
    finally: db.close()

if __name__ == "__main__": main()
