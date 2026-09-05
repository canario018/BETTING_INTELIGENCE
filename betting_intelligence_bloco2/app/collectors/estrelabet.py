from app.collectors.altenar import AltenarCouponCollector


class EstrelaBetCollector(AltenarCouponCollector):
    def __init__(self):
        super().__init__(
            sportsbook_name="EstrelaBet",
            integration="estrelabet",
            referer="https://www.estrelabet.bet.br/",
        )
