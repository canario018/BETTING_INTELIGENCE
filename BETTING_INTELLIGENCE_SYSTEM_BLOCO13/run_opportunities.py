from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import inspect, text

from app.config.settings import settings
from app.database.connection import Base, SessionLocal, engine
from app.database.migrations import ensure_schema as ensure_odds_schema, backfill_canonical_fields
from app.analytics.arbitrage import analyze_database
from app.opportunities.models import SurebetOpportunityModel, SurebetAlertModel
from app.opportunities.service import persist_opportunities, expire_old_opportunities, export_dashboard_json
from app.opportunities.temporal import update_lifetimes, calculate_bookmaker_ranking, persist_bookmaker_ranking


def ensure_schema() -> None:
    ensure_odds_schema()
    db0 = SessionLocal()
    try:
        backfill_canonical_fields(db0)
    finally:
        db0.close()
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("surebet_opportunities")}
    additions = {
        "opportunity_key": "VARCHAR(700)", "first_seen_at": "DATETIME", "last_seen_at": "DATETIME",
        "lifetime_seconds": "FLOAT DEFAULT 0", "times_seen": "INTEGER DEFAULT 1",
        "peak_profit_percent": "FLOAT DEFAULT 0", "trough_profit_percent": "FLOAT DEFAULT 0",
    }
    if engine.url.get_backend_name() == "sqlite":
        with engine.begin() as conn:
            for name, typ in additions.items():
                if name not in cols:
                    conn.execute(text(f"ALTER TABLE surebet_opportunities ADD COLUMN {name} {typ}"))


def main():
    parser = argparse.ArgumentParser(description="BLOCO 5 — histórico temporal, ranking e lifetime")
    parser.add_argument("--hours", type=int, default=settings.analysis_lookback_hours)
    parser.add_argument("--min-profit", type=float, default=settings.analysis_min_profit_percent)
    parser.add_argument("--bankroll", type=float, default=settings.bankroll)
    parser.add_argument("--max-age-seconds", type=int, default=180)
    parser.add_argument("--max-spread-seconds", type=int, default=30)
    parser.add_argument("--min-score", type=float, default=0)
    parser.add_argument("--expire-after-seconds", type=int, default=300)
    args = parser.parse_args()

    ensure_schema()
    db = SessionLocal()
    try:
        surebets = analyze_database(
            db, lookback_hours=args.hours, min_profit_percent=args.min_profit,
            max_age_seconds=args.max_age_seconds, max_timestamp_spread_seconds=args.max_spread_seconds,
            distinct_bookmakers=True, bankroll=args.bankroll,
        )
        from app.opportunities.service import reliability_score, alert_level
        surebets = [s for s in surebets if reliability_score(s) >= args.min_score]
        current_keys = {f"{s.event_key}|{s.market_type}|{s.line}" for s in surebets}

        created, updated = persist_opportunities(db, surebets, lookback_hours=args.hours)
        expired = update_lifetimes(db, current_keys, expire_after_seconds=args.expire_after_seconds)
        ranking = calculate_bookmaker_ranking(db, lookback_hours=args.hours)
        persist_bookmaker_ranking(db, ranking)
        export_dashboard_json(db, "data/opportunities/dashboard_opportunities.json")
        Path("data/opportunities/bookmaker_ranking.json").parent.mkdir(parents=True, exist_ok=True)
        Path("data/opportunities/bookmaker_ranking.json").write_text(json.dumps(ranking, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 110)
        print("BETTING INTELLIGENCE — BLOCO 5 / MARKET INTELLIGENCE")
        print("=" * 110)
        print(f"Surebets atuais: {len(surebets)} | novas: {created} | observações atualizadas: {updated} | expiradas: {expired}")
        for i, sb in enumerate(surebets, 1):
            print(f"#{i} [{alert_level(reliability_score(sb), sb.profit_percent)}] {sb.home_team} x {sb.away_team} | {sb.market_type} | ROI {sb.profit_percent:.3f}% | Score {reliability_score(sb):.1f}")
            print(f"   Frescor {sb.max_age_seconds:.1f}s | spread {sb.timestamp_spread_seconds:.1f}s | casas {sb.bookmaker_count}")
            for leg in sb.legs:
                print(f"   - {leg.bookmaker}: {leg.selection_code} @ {leg.odd:.4f}")
        print("\nRANKING DAS CASAS")
        for i, item in enumerate(ranking, 1):
            print(f"{i:02d}. {item['bookmaker']} | score {item['ranking_score']:.2f} | melhor odd {item['best_odd_rate']:.2f}% | pernas Surebet {item['surebet_leg_count']}")
        print("\nDatasets:")
        print("- data/opportunities/dashboard_opportunities.json")
        print("- data/opportunities/bookmaker_ranking.json")
        print("- SQLite: surebet_opportunities + surebet_observations + bookmaker_rankings")
        print("Alertas são informativos e locais; não há execução automática de apostas.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
