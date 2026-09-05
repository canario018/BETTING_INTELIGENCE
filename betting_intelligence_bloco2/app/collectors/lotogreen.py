from app.collectors.altenar import AltenarCouponCollector


class LotogreenCollector(AltenarCouponCollector):
    def __init__(self):
        super().__init__(
            sportsbook_name="Lotogreen",
            integration="lotogreen",
            referer="https://lotogreen.bet.br/",
        )
