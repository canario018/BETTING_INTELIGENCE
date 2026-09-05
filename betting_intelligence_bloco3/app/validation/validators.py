import logging

logger = logging.getLogger(__name__)

class OddsValidator:
    @staticmethod
    def is_valid_odds_record(data: dict) -> bool:
        try:
            if not data.get("home_team") or not data.get("away_team"):
                return False
            if float(data.get("odd", 0)) <= 1.0:
                return False
            if not data.get("market_name") or not data.get("selection_name"):
                return False
            return True
        except Exception as e:
            logger.warning(f"Falha na validação rigorosa do registro: {e}")
            return False
