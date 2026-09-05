from pathlib import Path
import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.collectors.altenar import AltenarCouponCollector
from app.database.connection import Base
from app.database.models import OddSnapshotModel
from app.database.repositories import OddsRepository

ROOT = Path(__file__).resolve().parent
FILES = [
    ("EstrelaBet", "estrelabet", "https://www.estrelabet.bet.br/", "resposta_bruta_estrelabet.json"),
    ("Lotogreen", "lotogreen", "https://lotogreen.bet.br/", "resposta_bruta_lotogreen.json"),
    ("Multibet", "multibet.br", "https://multi.bet.br/", "resposta_bruta_multibet.json"),
]

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()
repo = OddsRepository(db, 60)

total = 0
for bookmaker, integration, referer, filename in FILES:
    data = json.loads((ROOT / filename).read_text(encoding="utf-8"))
    collector = AltenarCouponCollector(bookmaker, integration, referer)
    records = collector.normalize_data(data)
    saved = sum(repo.save_snapshot(r) for r in records)
    total += saved
    print(f"{bookmaker}: {len(data.get('events', []))} eventos | {len(records)} odds normalizadas | {saved} gravadas")

rows = db.execute(select(OddSnapshotModel)).scalars().all()
print(f"TOTAL: {len(rows)} snapshots no SQLite de teste")
print("AMOSTRA:")
for row in rows[:5]:
    print(f"{row.bookmaker} | {row.home_team} x {row.away_team} | {row.market_type} | {row.selection_code} | {row.odd}")

assert total == len(rows) == 318
print("BLOCO 1 VALIDADO COM SUCESSO")
