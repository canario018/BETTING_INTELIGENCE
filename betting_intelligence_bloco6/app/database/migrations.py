from __future__ import annotations
from sqlalchemy import inspect, text
from app.database.connection import engine, Base
from app.database.models import OddSnapshotModel
from app.normalization.canonical import canonical_sport, canonical_market, canonical_selection, event_key, parse_event_start

ODDS_COLUMNS = {
    'event_start_at': 'DATETIME',
    'canonical_event_id': 'VARCHAR(255)',
    'canonical_sport': 'VARCHAR(50)',
    'canonical_market': 'VARCHAR(100)',
    'canonical_selection': 'VARCHAR(100)',
}

def ensure_schema():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    cols = {c['name'] for c in inspector.get_columns('odds_snapshots')}
    if engine.dialect.name == 'sqlite':
        with engine.begin() as conn:
            for name, typ in ODDS_COLUMNS.items():
                if name not in cols:
                    conn.execute(text(f'ALTER TABLE odds_snapshots ADD COLUMN {name} {typ}'))

def backfill_canonical_fields(db) -> int:
    rows = db.query(OddSnapshotModel).filter(OddSnapshotModel.canonical_event_id.is_(None)).all()
    count = 0
    for row in rows:
        row.event_start_at = parse_event_start(row.event_start_at)
        row.canonical_sport = canonical_sport(row.sport)
        row.canonical_market = canonical_market(row.market_type, row.sport)
        row.canonical_selection = canonical_selection(row.selection_name, row.selection_code)
        row.canonical_event_id = event_key(
            sport=row.sport, home_team=row.home_team, away_team=row.away_team,
            league=row.league, event_start_at=row.event_start_at,
        )
        count += 1
    if count:
        db.commit()
    return count
