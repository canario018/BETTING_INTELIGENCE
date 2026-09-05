from __future__ import annotations

import argparse

from app.analytics.arbitrage import analyze_database
from app.config.settings import settings
from app.database.connection import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Analisa surebets no SQLite")
    parser.add_argument("--hours", type=int, default=settings.analysis_lookback_hours)
    parser.add_argument("--min-profit", type=float, default=settings.analysis_min_profit_percent)
    parser.add_argument("--bankroll", type=float, default=settings.bankroll)
    parser.add_argument("--max-age-seconds", type=int, default=180,
                        help="Idade máxima de cada odd usada na oportunidade")
    parser.add_argument("--max-spread-seconds", type=int, default=30,
                        help="Diferença máxima entre timestamps das pernas")
    parser.add_argument("--allow-same-bookmaker", action="store_true",
                        help="Permite usar a mesma casa em mais de uma perna")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        results = analyze_database(
            db,
            lookback_hours=args.hours,
            min_profit_percent=args.min_profit,
            max_age_seconds=args.max_age_seconds,
            max_timestamp_spread_seconds=args.max_spread_seconds,
            distinct_bookmakers=not args.allow_same_bookmaker,
            bankroll=args.bankroll,
        )
    finally:
        db.close()

    print("=" * 112)
    print("BETTING INTELLIGENCE — SUREBET ENGINE PROFISSIONAL")
    print("=" * 112)
    print(
        f"Janela: {args.hours}h | ROI mínimo: {args.min_profit:.2f}% | "
        f"idade máx.: {args.max_age_seconds}s | spread máx.: {args.max_spread_seconds}s | "
        f"Banca: R$ {args.bankroll:,.2f}"
    )
    print(f"Surebets válidas: {len(results)}")

    for i, sb in enumerate(results, 1):
        print("\n" + "-" * 112)
        print(f"#{i} {sb.home_team} x {sb.away_team} | {sb.market_type} | linha={sb.line}")
        print(
            f"Σ(1/odd)={sb.probability_sum:.8f} | ROI={sb.profit_percent:.3f}% | "
            f"casas={sb.bookmaker_count} | odd mínima={sb.min_odd:.4f}"
        )
        print(
            f"Frescor: maior idade={sb.max_age_seconds:.1f}s | "
            f"spread entre pernas={sb.timestamp_spread_seconds:.1f}s"
        )
        stakes = sb.stakes(args.bankroll)
        for leg in sb.legs:
            print(
                f"  {leg.bookmaker:<14} {leg.selection_code:<8} "
                f"odd={leg.odd:.4f} stake=R$ {stakes[leg.selection_code]:,.2f}"
            )
        print(
            f"Retorno garantido teórico: R$ {sb.guaranteed_return:,.2f} | "
            f"Lucro teórico: R$ {sb.guaranteed_profit:,.2f}"
        )

    if not results:
        print("\nNenhuma surebet válida encontrada com os filtros atuais.")
        print("O motor não considera uma oportunidade válida quando o mercado está incompleto, desatualizado ou Σ(1/odd) >= 1.")


if __name__ == "__main__":
    main()
