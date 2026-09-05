from __future__ import annotations

import json
import logging

import requests
from sqlalchemy.orm import Session

from app.opportunities.models import SurebetAlertModel, SurebetOpportunityModel

logger = logging.getLogger("ALERTS.TELEGRAM")

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramNotifier:
    """Envia alertas de oportunidades para um chat/canal do Telegram.

    Só notifica — nunca executa, confirma ou automatiza uma aposta. Falhas
    de rede são logadas e não derrubam o pipeline principal; o alerta
    permanece marcado como não entregue para ser reenviado no próximo ciclo.
    """

    def __init__(self, bot_token: str, chat_id: str, timeout: int = 10):
        if not bot_token or not chat_id:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID são obrigatórios para ativar os alertas."
            )
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout

    def send_message(self, text: str) -> bool:
        url = f"{TELEGRAM_API_BASE}/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                return True
            logger.error("Telegram respondeu %s: %s", response.status_code, response.text[:300])
            return False
        except requests.RequestException as exc:
            logger.error("Falha de conexão ao enviar alerta Telegram: %s", exc)
            return False


def _escape(value: str | None) -> str:
    return (value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _calculate_stakes(legs: list[dict], bankroll: float, probability_sum: float) -> dict[str, float]:
    """Stake por seleção, proporcional a 1/odd — mesma lógica de Surebet.stakes()."""
    if not bankroll or not probability_sum:
        return {leg["selection_code"]: 0.0 for leg in legs}
    return {
        leg["selection_code"]: bankroll * (1.0 / leg["odd"]) / probability_sum
        for leg in legs
    }


def format_opportunity_message(row: SurebetOpportunityModel) -> str:
    """Formata uma linha de surebet_opportunities em mensagem HTML para o Telegram."""
    legs = json.loads(row.legs_json)
    stakes = _calculate_stakes(legs, row.bankroll, row.probability_sum)

    header = f"🎯 <b>[{_escape(row.alert_level)}] Surebet detectada</b>"
    event_line = f"⚽ <b>{_escape(row.home_team)} x {_escape(row.away_team)}</b>"
    market_line = f"📊 {_escape(row.market_type)}"
    if row.line is not None:
        market_line += f" (linha {row.line})"
    roi_line = (
        f"💰 ROI: <b>{row.profit_percent:.2f}%</b> | "
        f"Lucro garantido: R$ {row.guaranteed_profit:.2f} (banca R$ {row.bankroll:.2f})"
    )
    score_line = (
        f"🔎 Confiabilidade: {row.reliability_score:.0f}/100 | "
        f"Frescor: {row.max_age_seconds:.0f}s | Casas: {row.bookmaker_count}"
    )

    legs_lines = []
    for leg in legs:
        stake = stakes.get(leg["selection_code"], 0.0)
        nome_selecao = leg.get("selection_name") or leg["selection_code"]
        legs_lines.append(
            f"  • <b>{_escape(leg['bookmaker'])}</b> — {_escape(nome_selecao)} "
            f"@ {leg['odd']:.3f} → apostar <b>R$ {stake:.2f}</b>"
        )

    footer = "⚠️ Alerta informativo. Confira as odds na casa antes de apostar — elas mudam rápido e o robô não aposta por você."

    return "\n".join([header, event_line, market_line, roi_line, score_line, "", *legs_lines, "", footer])


def send_pending_alerts(db: Session, notifier: TelegramNotifier, limit: int = 20) -> tuple[int, int]:
    """Envia alertas ainda não entregues (SurebetAlertModel.delivered == 0).

    Retorna (enviados, falhas). Alertas cuja oportunidade não existe mais
    são marcados como entregues sem reenvio (evita loop infinito de erro).
    """
    pending = (
        db.query(SurebetAlertModel)
        .filter(SurebetAlertModel.delivered == 0)
        .order_by(SurebetAlertModel.created_at.asc())
        .limit(limit)
        .all()
    )
    sent = failed = 0
    for alert in pending:
        opportunity = (
            db.query(SurebetOpportunityModel)
            .filter_by(id=alert.opportunity_id)
            .first()
        )
        if opportunity is None:
            alert.delivered = 1
            continue
        message = format_opportunity_message(opportunity)
        if notifier.send_message(message):
            alert.delivered = 1
            sent += 1
        else:
            failed += 1
    db.commit()
    return sent, failed
