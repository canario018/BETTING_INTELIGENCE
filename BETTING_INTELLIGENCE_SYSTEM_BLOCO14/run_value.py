from app.config.settings import settings
from app.database.connection import SessionLocal
from app.value.engine import analyze_database
from app.value.persistence import persist_value_opportunities

def main():
    db=SessionLocal()
    try:
        ops=analyze_database(db, lookback_hours=settings.analysis_lookback_hours, min_ev_percent=3.0, min_edge_percent=1.0, min_bookmakers=2, max_age_seconds=300)
        saved=persist_value_opportunities(db, ops) if ops else 0
        print({"opportunities":len(ops),"saved":saved})
        for op in ops[:20]: print(f"{op.market_type} | {op.home_team} x {op.away_team} | {op.bookmaker} | {op.selection_code} @ {op.odd:.2f} | fair {op.fair_odd:.2f} | EV {op.expected_value_percent:.2f}% | edge {op.edge_percent:.2f}pp")
    finally: db.close()
if __name__=='__main__': main()
