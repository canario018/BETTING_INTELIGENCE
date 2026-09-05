# BLOCO 3 — SUREBET ENGINE PROFISSIONAL

Este bloco transforma o motor inicial em uma camada de análise mais rigorosa sobre o SQLite.

## O que entrou

### 1. Matching conservador de eventos
A identificação deixa de depender apenas do `event_id` da casa. A chave usa esporte + equipes normalizadas + mercado + linha. Sufixos genéricos como `FC`, `SC` e `Club` são removidos somente para comparação.

Não há fuzzy matching: o objetivo é evitar falsos positivos.

### 2. Melhor odd por seleção
Para cada evento/mercado/resultado, o motor considera a maior odd disponível entre as casas.

### 3. Mercado completo
Somente mercados com universo conhecido são analisados:

- `MATCH_RESULT`: HOME / DRAW / AWAY
- `TOTAL_GOALS`: OVER / UNDER
- `BOTH_TEAMS_TO_SCORE`: YES / NO

Mercado incompleto é descartado.

### 4. Frescor das odds
Por padrão, cada perna precisa ter no máximo 180 segundos e o maior intervalo entre timestamps não pode passar de 30 segundos.

Isso reduz oportunidades matematicamente corretas, mas operacionalmente defasadas.

### 5. Restrição de casas
Por padrão, uma mesma bookmaker não pode ocupar duas pernas do mesmo surebet.

### 6. Cálculo profissional de stake
Para banca `B` e odd `O_i`:

`stake_i = B × (1/O_i) / Σ(1/O)`

O retorno teórico comum é:

`retorno = B / Σ(1/O)`

E o lucro teórico:

`lucro = retorno - B`

### 7. Ranking
As oportunidades são ordenadas pelo ROI teórico, com desempates por odd mínima e frescor.

## Execução

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
python main.py
python inspect_db.py
python run_analysis.py
```

Para uma análise mais permissiva de histórico:

```powershell
python run_analysis.py --hours 24 --min-profit 0.10 --bankroll 1000 --max-age-seconds 600 --max-spread-seconds 120
```

## Interpretação

Uma surebet exige `Σ(1/odd) < 1`. O número pode ser zero mesmo com centenas de odds no banco; isso significa apenas que não houve arbitragem válida sob os filtros aplicados.

## Limite operacional

Este é um motor analítico. Antes de qualquer decisão, valide manualmente equivalência de período, linha, regras de liquidação, status da cotação, limites e disponibilidade. O projeto não automatiza apostas, login, CAPTCHA ou contorno de restrições.
