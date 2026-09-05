from app.database.connection import SessionLocal
from app.database.migrations import ensure_schema, backfill_canonical_fields
from app.database.models import OddSnapshotModel

def main():
    ensure_schema()
    db=SessionLocal()
    try:
        backfill_canonical_fields(db)
        rows=db.query(OddSnapshotModel).order_by(OddSnapshotModel.collected_at.desc()).limit(20).all()
        for r in rows:
            print(f'{r.bookmaker:15} | {r.canonical_sport:12} | {r.canonical_event_id} | {r.canonical_market} | {r.canonical_selection} | {r.odd}')
    finally: db.close()
if __name__=='__main__': main()
