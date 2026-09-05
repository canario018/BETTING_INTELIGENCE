# BLOCO 6 — Canonical Market + Event Matching + Fundação Multi-Esporte

## Objetivo
Transformar os dados coletados por cada bookmaker em uma identidade comum para que o motor consiga comparar casas sem depender do texto bruto usado por cada fonte.

## Entregas
- `app/normalization/canonical.py`: normalização canônica de esporte, equipe, mercado, seleção, linha e evento.
- `app/matching/event_matcher.py`: matching conservador de eventos, usando esporte + equipes na mesma orientação + horário do evento quando disponível.
- `app/matching/market_matcher.py`: matching por mercado/linha e seleção canônicos.
- `event_start_at` persistido em `odds_snapshots`.
- `canonical_event_id`, `canonical_sport`, `canonical_market`, `canonical_selection` persistidos em `odds_snapshots`.
- migração/backfill automático para SQLite existente.
- Altenar agora extrai `event.startDate` dos payloads reais já usados pelo projeto.
- `arbitrage.py` passa a priorizar `canonical_event_id`, mantendo fallback para bancos antigos.
- base de aliases para Futebol, Basquete, Tênis, Vôlei, Handebol, Hóquei, Beisebol e Futsal.
- base de mercados comuns, sem afirmar que todos são elegíveis para arbitragem ainda.

## Regra de segurança do matching
O BLOCO 6 é deliberadamente conservador. Não utiliza fuzzy matching. A orientação casa/fora é preservada, porque `HOME` e `AWAY` têm significado diferente no cálculo de uma arbitragem. Quando o horário do evento existe, uma divergência acima da tolerância padrão de 120 segundos rejeita o match.

A liga não faz parte do `canonical_event_id`, pois nomes de competições podem variar entre bookmakers. Ela continua armazenada para análise e auditoria.

## Multi-esporte
A fundação permite normalizar novos esportes sem alterar o modelo de banco. O motor de arbitragem continua limitado aos mercados com universo de resultados formalmente suportado. Novos mercados devem ser adicionados somente depois de definirmos corretamente suas regras de liquidação.

## Testes
```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```
Resultado validado no pacote: **23 passed**.

## Execução
```powershell
python main.py
python run_opportunities.py --hours 24 --min-profit 0.10 --bankroll 1000
```

## Inspeção rápida
Depois de uma coleta real, os registros passam a ter campos como:
```text
sport = Futebol
canonical_sport = FOOTBALL
home_team = Criciúma
away_team = Cuiabá
canonical_event_id = FOOTBALL|criciuma|cuiaba|202609042230
market_type = MATCH_RESULT
canonical_market = MATCH_RESULT
selection_code = HOME
canonical_selection = HOME
```

O sistema permanece analítico: não executa apostas automaticamente, não faz login, não contorna CAPTCHA e não tenta burlar mecanismos de proteção.
