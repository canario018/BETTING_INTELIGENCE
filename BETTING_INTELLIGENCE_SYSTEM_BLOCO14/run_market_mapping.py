from __future__ import annotations
import argparse, json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
from app.database.models import OddSnapshotModel
from app.market_mapping import build_market_matrix, cross_book_opportunities


def main():
    ap=argparse.ArgumentParser(description='Market Mapping Engine')
    ap.add_argument('--minutes',type=int,default=15)
    ap.add_argument('--min-bookmakers',type=int,default=2)
    ap.add_argument('--markets',nargs='*',default=None)
    ap.add_argument('--json',default='data/market_mapping.json')
    args=ap.parse_args()
    engine=create_engine(settings.database_url)
    Session=sessionmaker(bind=engine)
    db=Session()
    try:
        since=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(minutes=args.minutes)
        rows=db.query(OddSnapshotModel).filter(OddSnapshotModel.collected_at>=since).all()
        matrix=build_market_matrix(rows, max_age_seconds=args.minutes*60, markets=set(args.markets) if args.markets else None)
        opps=cross_book_opportunities(matrix,args.min_bookmakers)
        payload={'generated_at':datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),'rows':len(matrix),'complete_markets':sum(x.complete for x in matrix),'surebets':sum(x['is_surebet'] for x in opps),'cross_book':opps,'matrix':[x.__dict__ for x in matrix]}
        Path(args.json).parent.mkdir(parents=True,exist_ok=True)
        Path(args.json).write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        print('='*110); print('BETTING INTELLIGENCE SYSTEM - MARKET MAPPING ENGINE'); print('='*110)
        print(f'snapshots={len(rows)} | market_rows={len(matrix)} | completos={payload["complete_markets"]} | surebets={payload["surebets"]}')
        for x in opps[:30]:
            flag='SUREBET' if x['is_surebet'] else 'MARKET'
            print(f"{flag:7} {x['home']} x {x['away']} | {x['market']} {x['line']} | books={x['bookmakers']} | ROI={x['arbitrage_roi_percent']:.2f}% | sum={x['probability_sum']:.5f}")
            for leg in x['legs']: print(f"   {leg['selection']:5} {leg['best_odd']:.3f} @ {leg['bookmaker']}")
        print(f'JSON: {Path(args.json).resolve()}')
    finally: db.close()
if __name__=='__main__': main()
