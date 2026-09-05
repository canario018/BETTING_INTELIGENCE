from __future__ import annotations

import argparse
from app.config.settings import settings
from app.database.connection import Base, SessionLocal, engine
from app.analytics.arbitrage import analyze_database
from app.opportunities.models import SurebetOpportunityModel, SurebetAlertModel
from app.opportunities.service import persist_opportunities, expire_old_opportunities, export_dashboard_json


def main():
    parser = argparse.ArgumentParser(description="Pipeline profissional de oportunidades Surebet")
    parser.add_argument("--hours", type=int, default=settings.analysis_lookback_hours)
    parser.add_argument("--min-profit", type=float, default=settings.analysis_min_profit_percent)
    parser.add_argument("--bankroll", type=float, default=settings.bankroll)
    parser.add_argument("--max-age-seconds", type=int, default=180)
    parser.add_argument("--max-spread-seconds", type=int, default=30)
    parser.add_argument("--min-score", type=float, default=0)
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        surebets = analyze_database(db, lookback_hours=args.hours, min_profit_percent=args.min_profit,
                                    max_age_seconds=args.max_age_seconds,
                                    max_timestamp_spread_seconds=args.max_spread_seconds,
                                    distinct_bookmakers=True, bankroll=args.bankroll)
        surebets = [s for s in surebets if __import__('app.opportunities.service', fromlist=['reliability_score']).reliability_score(s) >= args.min_score]
        created, updated = persist_opportunities(db, surebets, lookback_hours=args.hours)
        expired = expire_old_opportunities(db, max_age_seconds=max(300, args.max_age_seconds * 2))
        export_dashboard_json(db, "data/opportunities/dashboard_opportunities.json")
        alerts = db.query(SurebetAlertModel).order_by(SurebetAlertModel.created_at.desc()).limit(10).all()
        print("=" * 100)
        print("BETTING INTELLIGENCE — OPPORTUNITY CENTER")
        print("=" * 100)
        print(f"Surebets atuais: {len(surebets)} | novas: {created} | atualizadas: {updated} | expiradas: {expired}")
        for i, sb in enumerate(surebets, 1):
            from app.opportunities.service import reliability_score, alert_level
            print(f"#{i} [{alert_level(reliability_score(sb), sb.profit_percent)}] {sb.home_team} x {sb.away_team} | {sb.market_type} | ROI {sb.profit_percent:.3f}% | Score {reliability_score(sb):.1f}")
            print(f"   Frescor {sb.max_age_seconds:.1f}s | spread {sb.timestamp_spread_seconds:.1f}s | casas {sb.bookmaker_count}")
            for leg in sb.legs:
                print(f"   - {leg.bookmaker}: {leg.selection_code} @ {leg.odd:.4f}")
        print(f"\nDataset: data/opportunities/dashboard_opportunities.json")
        print("Alertas são informativos e locais; não há execução automática de apostas.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
