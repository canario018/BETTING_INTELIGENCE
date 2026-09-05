# Executar BLOCO 5

1. Ative o ambiente:
```powershell
.\.venv\Scripts\Activate.ps1
```

2. Valide:
```powershell
python -m pytest -q
```

3. Colete odds reais:
```powershell
python main.py
```

4. Gere oportunidades, histórico, movimentação e ranking:
```powershell
python run_opportunities.py --hours 24 --min-profit 0.10 --bankroll 1000
```

5. Consulte os arquivos:
- `data/opportunities/dashboard_opportunities.json`
- `data/opportunities/bookmaker_ranking.json`

6. Se quiser diagnosticar oportunidades mais antigas:
```powershell
python run_opportunities.py --hours 24 --min-profit 0.10 --bankroll 1000 --max-age-seconds 600 --max-spread-seconds 120
```

`lifetime_seconds` só cresce quando a mesma oportunidade é observada novamente. Uma oportunidade ausente por mais que `--expire-after-seconds` passa para `EXPIRED`.
