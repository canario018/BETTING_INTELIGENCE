# EXECUTAR BLOCO 14

1. Faça backup de `data\betting.db`.
2. Substitua sua pasta do projeto pela versão do BLOCO 14, preservando `.env` e `data\betting.db`.
3. Ative o ambiente virtual.
4. Execute:

```powershell
python -m compileall -q app run_market_mapping.py
pytest -q
```

5. Confirme os coletores:
```powershell
python -c "from app.config.settings import settings; print(settings.collectors)"
```

6. Faça uma coleta:
```powershell
python main.py
```

7. Rode o mapeamento:
```powershell
python run_market_mapping.py --minutes 15 --min-bookmakers 2
```

8. O resultado fica em `data\market_mapping.json`.

9. Para restringir aos mercados principais:
```powershell
python run_market_mapping.py --minutes 15 --markets MATCH_RESULT TOTAL_GOALS BOTH_TEAMS_TO_SCORE HANDICAP
```

10. Interpretação:
- `complete_markets`: universo de seleções fechado;
- `surebets`: somente quando soma das probabilidades implícitas das melhores odds < 1;
- `MARKET`: mercado comparável, mas sem arbitragem garantida;
- `OTHER`: permanece fora do cálculo.

### Importante
O parser R7Bet/Bet.Bet foi construído a partir da estrutura real observada nos RAWs, não por tentativa de inventar campos. Se a API mudar, o health deve indicar alteração e o RAW deve ser inspecionado antes de alterar o parser.
