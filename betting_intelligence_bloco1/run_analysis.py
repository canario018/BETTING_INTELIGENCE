from __future__ import annotations

import argparse

from app.analytics.arbitrage import analyze_database
from app.config.settings import settings
from app.database.connection import SessionLocal


def main():
    parser = argparse.ArgumentParser(description="Analisa surebets no SQLite")
    parser.add_argument("--hours", type=int, default=settings.analysis_lookback_hours)
    parser.add_argument("--min-profit", type=float, default=settings.analysis_min_profit_percent)
    parser.add_argument("--bankroll", type=float, default=settings.bankroll)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        results = analyze_database(db, args.hours, args.min_profit)
    finally:
        db.close()

    print("=" * 100)
    print("BETTING INTELLIGENCE - SUREBET ENGINE")
    print("=" * 100)
    print(f"Janela: {args.hours}h | ROI mínimo: {args.min_profit:.2f}% | Banca: R$ {args.bankroll:,.2f}")
    print(f"Surebets encontradas: {len(results)}")

    for i, sb in enumerate(results, 1):
        print("\n" + "-" * 100)
        print(f"#{i} {sb.home_team} x {sb.away_team} | {sb.market_type} | linha={sb.line}")
        print(f"Σ(1/odd) = {sb.probability_sum:.6f} | ROI teórico = {sb.profit_percent:.2f}%")
        for leg in sb.legs:
            stake = args.bankroll * (1.0 / leg.odd) / sb.probability_sum
            print(f"  {leg.bookmaker:<14} {leg.selection_code:<8} odd={leg.odd:.4f} stake=R$ {stake:,.2f}")
        retorno = args.bankroll / sb.probability_sum
        print(f"Retorno teórico comum: R$ {retorno:,.2f}")

    if not results:
        print("\nNenhuma surebet válida encontrada na janela analisada.")
        print("Isso é um resultado normal; o sistema não inventa oportunidade quando Σ(1/odd) >= 1.")


if __name__ == "__main__":
    main()
