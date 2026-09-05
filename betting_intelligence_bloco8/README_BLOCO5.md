# BLOCO 5 — Market Intelligence

Este bloco evolui o Opportunity Center para uma camada temporal e histórica.

## Entregas
- histórico de observações de cada oportunidade;
- identidade estável (`opportunity_key`) separada do fingerprint das odds;
- `first_seen_at`, `last_seen_at`, `lifetime_seconds`, `times_seen`;
- pico e piso de ROI;
- série temporal de odds por bookmaker/seleção;
- direção, delta, delta %, velocidade por minuto e volatilidade;
- ranking de bookmakers por frequência de melhor odd e participação nas pernas de Surebet;
- export JSON para dashboard;
- migração automática de colunas novas em SQLite existente.

## Execução
```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
python main.py
python run_opportunities.py --hours 24 --min-profit 0.10 --bankroll 1000
```

Arquivos gerados:
- `data/opportunities/dashboard_opportunities.json`
- `data/opportunities/bookmaker_ranking.json`

O sistema é analítico e não executa apostas automaticamente.
