from __future__ import annotations

import logging

from app.collectors.apostaganha import ApostaGanhaCollector
from app.collectors.betano import BetanoCollector
from app.collectors.estrelabet import EstrelaBetCollector
from app.collectors.lotogreen import LotogreenCollector
from app.collectors.multibet import MultibetCollector
from app.collectors.novibet import NovibetCollector
from app.collectors.superbet import SuperbetCollector
from app.collectors.onabet import OnabetCollector
from app.collectors.r7bet import R7BetCollector
from app.collectors.betbet import BetBetCollector
from app.collectors.vbet import VBetCollector
from app.collectors.kbet7 import KBet7Collector

logger = logging.getLogger("COLLECTORS")


def build_collectors(settings):
    names = [x.strip().lower() for x in settings.collectors.split(",") if x.strip()]
    factories = {
        "estrelabet": lambda: EstrelaBetCollector(timeout=settings.request_timeout_seconds),
        "lotogreen": lambda: LotogreenCollector(timeout=settings.request_timeout_seconds),
        "multibet": lambda: MultibetCollector(timeout=settings.request_timeout_seconds),
        "apostaganha": ApostaGanhaCollector,
        "onabet": lambda: OnabetCollector(timeout=settings.request_timeout_seconds),
        "r7bet": lambda: R7BetCollector(timeout=settings.request_timeout_seconds, api_endpoint=settings.r7bet_api_endpoint or None),
        "betbet": lambda: BetBetCollector(timeout=settings.request_timeout_seconds, api_endpoint=settings.betbet_api_endpoint or None),
        "vbet": lambda: VBetCollector(timeout=settings.request_timeout_seconds, api_endpoint=settings.vbet_api_endpoint or None),
        "7kbet": lambda: KBet7Collector(timeout=settings.request_timeout_seconds, api_endpoint=settings.kbet7_api_endpoint or None),
        "betano": lambda: BetanoCollector(api_endpoint=settings.betano_api_endpoint or None),
        "superbet": lambda: SuperbetCollector(settings.superbet_api_endpoint),
        "novibet": lambda: NovibetCollector(settings.novibet_api_endpoint),
    }
    collectors = []
    for name in names:
        factory = factories.get(name)
        if not factory:
            logger.warning("Collector desconhecido ignorado: %s", name)
            continue
        try:
            collectors.append(factory())
        except ValueError as exc:
            logger.warning("Collector %s não ativado: %s", name, exc)
    return collectors
