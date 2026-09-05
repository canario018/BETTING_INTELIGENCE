from __future__ import annotations

from sqlalchemy import func
from app.database.connection import SessionLocal
from app.database.models import OddSnapshotModel


def main():
    db = SessionLocal()
    try:
        total = db.query(func.count(OddSnapshotModel.id)).scalar() or 0
        print("=" * 90)
        print("AUDITORIA DO SQLITE")
        print("=" * 90)
        print(f"Total de snapshots: {total}")

        rows = (
            db.query(OddSnapshotModel)
            .order_by(OddSnapshotModel.collected_at.desc(), OddSnapshotModel.bookmaker)
            .limit(30)
            .all()
        )
        print(f"\n{'CASA':<14} | {'EVENTO':<38} | {'MERCADO':<18} | {'SEL.':<8} | ODD")
        print("-" * 90)
        for r in rows:
            event = f"{r.home_team} x {r.away_team}"
            print(f"{r.bookmaker[:14]:<14} | {event[:38]:<38} | {r.market_type[:18]:<18} | {r.selection_code[:8]:<8} | {r.odd:.4f}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
