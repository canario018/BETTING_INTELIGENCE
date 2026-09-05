from __future__ import annotations

import logging

from app.collectors.apostaganha import ApostaGanhaCollector
from app.collectors.betano import BetanoCollector
from app.collectors.estrelabet import EstrelaBetCollector
from app.collectors.lotogreen import LotogreenCollector
from app.collectors.multibet import MultibetCollector
from app.collectors.novibet import NovibetCollector
from app.collectors.superbet import SuperbetCollector

logger = logging.getLogger("COLLECTORS")


def build_collectors(settings):
    names = [x.strip().lower() for x in settings.collectors.split(",") if x.strip()]
    factories = {
        "estrelabet": EstrelaBetCollector,
        "lotogreen": LotogreenCollector,
        "multibet": MultibetCollector,
        "apostaganha": ApostaGanhaCollector,
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
