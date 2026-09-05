# EXECUTAR BLOCO 7

1. Abra PowerShell na pasta do projeto.
2. Ative o ambiente virtual.
3. Execute:

```powershell
python -m pytest -q
python run_temporal.py --hours 120 --windows 24 48 72 96 120
```

4. Confira:
- `data/opportunities/temporal_intelligence.json`
- tabela SQLite `temporal_market_stats`

O engine é somente analítico; não executa apostas.
