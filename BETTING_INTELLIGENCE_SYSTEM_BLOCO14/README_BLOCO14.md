# BLOCO 14 — Market Mapping Engine

Este bloco transforma odds normalizadas em uma matriz comparável entre casas.

## Entregas
- parser específico SportsData para R7Bet e Bet.Bet;
- leitura de `Events -> Markets -> Selections`;
- identificação de participante Home/Away;
- suporte a `ML0`, `ML1`, `OU*`, `HC*` e nomes observados;
- preservação de linha (`line`) para totais/handicap;
- matriz evento x mercado x linha x seleção x bookmaker;
- melhor odd por seleção;
- quantidade de casas por mercado;
- identificação de mercados completos;
- cálculo de divergência/arbitragem apenas em universos fechados;
- exportação JSON.

## Regra de segurança analítica
`OTHER` e mercados incompletos não entram no cálculo de surebet. Handicap só é comparado quando a linha é igual. Não há automação de apostas.

## Execução
```powershell
python -m compileall -q app run_market_mapping.py
pytest -q
python run_collector_health.py
python run_market_mapping.py --minutes 15 --min-bookmakers 2
```

## Observação
R7Bet e Bet.Bet retornaram HTTP 200 mas o parser genérico não reconhecia a estrutura; os payloads reais mostram `Events`, `Participants`, `Markets`, `MarketType` e `Selections`, por isso agora possuem parser dedicado. 7KBet continua separado quando responder 403 e VBET continua sem ser tratado como feed de odds enquanto o endpoint observado retornar apenas configuração de page-builder.
