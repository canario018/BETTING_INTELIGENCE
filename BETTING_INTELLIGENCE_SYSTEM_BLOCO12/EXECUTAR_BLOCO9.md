# BLOCO 9 — Opportunity Ranking + Intelligence Center

## 1. Testar
```powershell
python -m pytest -q
```

## 2. Executar
```powershell
python run_intelligence_center.py --hours 120 --windows 24 48 72 96 120 --min-strength 40 --top 50 --bankroll 1000
```

## 3. Saída
- `data/opportunities/intelligence_center.json`
- SQLite: `opportunity_rankings`

O ranking é uma prioridade analítica baseada nas evidências disponíveis. Não representa probabilidade de vitória e não executa apostas.
