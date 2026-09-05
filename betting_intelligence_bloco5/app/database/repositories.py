import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.database.models import OddSnapshotModel

logger = logging.getLogger(__name__)


class OddsRepository:
    def __init__(self, db: Session, idempotency_window_seconds: int = 60):
        self.db = db
        self.idempotency_window_seconds = idempotency_window_seconds

    def save_snapshot(self, data: dict) -> bool:
        collected_at = data.get("collected_at") or datetime.now(timezone.utc)
        if collected_at.tzinfo is None:
            collected_at = collected_at.replace(tzinfo=timezone.utc)

        bookmaker = data.get("bookmaker") or data.get("sportsbook") or "Desconhecida"
        event_id = str(data.get("event_id") or "N/A")
        market_name = data.get("market_name") or "N/A"
        selection_code = data.get("selection_code") or data.get("selection_name") or "N/A"
        line = data.get("line")
        odd = float(data.get("odd") or data.get("odd_value") or data.get("price") or 0.0)
        if odd <= 1.0:
            return False

        # Idempotência: só bloqueia uma repetição realmente recente da mesma cotação.
        cutoff = collected_at - timedelta(seconds=self.idempotency_window_seconds)
        duplicate = self.db.query(OddSnapshotModel).filter(
            OddSnapshotModel.bookmaker == bookmaker,
            OddSnapshotModel.event_id == event_id,
            OddSnapshotModel.market_name == market_name,
            OddSnapshotModel.selection_code == selection_code,
            OddSnapshotModel.line == line,
            OddSnapshotModel.odd == odd,
            OddSnapshotModel.collected_at >= cutoff,
        ).first()
        if duplicate:
            return False

        snapshot_data = {
            "collected_at": collected_at.replace(tzinfo=None),
            "bookmaker": bookmaker,
            "source_url": data.get("source_url") or "unknown",
            "sport": data.get("sport") or "Futebol",
            "league": data.get("league") or "Geral",
            "event_id": event_id,
            "home_team": data.get("home_team") or "Home",
            "away_team": data.get("away_team") or "Away",
            "market_name": market_name,
            "market_type": data.get("market_type") or "OTHER",
            "selection_name": data.get("selection_name") or "N/A",
            "selection_code": selection_code,
            "line": line,
            "odd": odd,
            "currency": data.get("currency") or "BRL",
            "raw_key": data.get("raw_key") or f"{bookmaker}|{event_id}|{market_name}|{selection_code}|{line}",
        }
        try:
            self.db.add(OddSnapshotModel(**snapshot_data))
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            logger.exception("Erro ao salvar snapshot no banco")
            raise
