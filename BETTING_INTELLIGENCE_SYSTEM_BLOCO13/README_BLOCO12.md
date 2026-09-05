# BLOCO 12 — Hardening + API Health + Value Intelligence

Este bloco evolui o sistema existente sem automatizar apostas.

## O que foi implementado

1. **Collector Health**
   - status por casa
   - HTTP status
   - latência
   - quantidade de registros normalizados
   - bytes da resposta
   - erro por collector
2. **Value Betting baseline**
   - probabilidade implícita
   - desvigamento do mercado (de-vig)
   - probabilidade justa de consenso
   - fair odd
   - edge em pontos percentuais
   - EV/ROI esperado
   - confiança de cobertura
3. **Persistência SQLite**
   - `value_opportunities`
   - `value_observations`
   - `monitor_runs.value_opportunities_count`
4. **Integração com o monitor**
   - cada ciclo passa a calcular Value Bets após salvar os snapshots
5. **Telegram**
   - além de SUREBET e MARKET_CHANGE, o motor pode gerar `VALUE_BET`
6. **DB Browser for SQLite**
   - todas as análises são persistidas no mesmo `data/betting.db`.

## Importante sobre Value Betting

O motor deste bloco usa **consenso do mercado**, não uma previsão independente. Portanto, `EV positivo` aqui significa que a odd está acima do preço justo estimado pelo consenso das casas participantes. Isso é um sinal de valor, não garantia de ROI realizado.

Para afirmar valor estatístico independente, o próximo bloco deve adicionar modelos de probabilidade e backtest/CLV.

## Limites atuais

- Superbet e Novibet continuam desativadas até que endpoints reais e autorizados sejam configurados.
- O endpoint da Betano existente no projeto deve ser validado no ambiente real; presença de código não prova que a fonte esteja atualizada.
- Nenhum login, CAPTCHA bypass, anti-bot bypass ou execução automática de aposta é implementado.

## Correção de inicialização — BLOCO 12

Foi incluída uma correção de migração para garantir que `Base.metadata.create_all()` seja executado antes de qualquer `ALTER TABLE`. Isso evita `sqlite3.OperationalError: no such table: monitor_runs` em bancos novos ou parcialmente inicializados. Também foi removido o risco de importar `OpportunityRankingModel` do módulo incorreto `app.intelligence_center`; o model de persistência é registrado por `app.intelligence_persistence`.

Consulte `CORRECAO_BLOCO12.md` e `EXECUTAR_CORRECAO_BLOCO12.md` para o procedimento.
