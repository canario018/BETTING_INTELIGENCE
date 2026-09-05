# BLOCO 8 — Market Intelligence + Signal Engine

O BLOCO 8 combina três camadas já construídas no sistema:

1. **estado atual** das odds;
2. **histórico temporal** de 24/48/72/96/120h;
3. **estado atual de Surebet** com os filtros de frescor e sincronização do BLOCO 3–5.

A saída é um **sinal analítico**, não uma ordem de execução.

## Sinais

- `SUREBET`: mercado atualmente satisfaz a condição matemática de arbitragem e a seleção participa da configuração encontrada.
- `STRONG_DOWN`: movimento histórico consistente de queda da odd.
- `STRONG_UP`: movimento histórico consistente de alta da odd.
- `ANOMALY`: último valor estatisticamente atípico em relação à série.
- `CROSS_BOOK_DIVERGENCE`: dispersão relevante entre casas no snapshot mais recente.
- `STABLE_MARKET`: ausência de movimento suficientemente forte.

## Score

`strength` combina movimento temporal, divergência entre casas e frescor. `confidence` combina frescor, número de amostras, anomalia e cobertura de casas. São scores de priorização analítica; não representam probabilidade de acerto.

## Execução

```powershell
python -m pytest -q
python run_signals.py --hours 120 --windows 24 48 72 96 120 --min-strength 40 --bankroll 1000
```

Saída:

`data/opportunities/market_signals.json`

Histórico persistido:

`market_signals`

## Limites deliberados

O motor não faz login, CAPTCHA bypass, anti-bot, execução automática de apostas ou qualquer contorno de restrição. Mercados novos só devem ser habilitados para arbitragem quando suas regras de liquidação estiverem formalmente modeladas.
