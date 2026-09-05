# BLOCO 7 — TEMPORAL INTELLIGENCE ENGINE

Transforma snapshots de odds em inteligência histórica para 24/48/72/96/120 horas.

## O que entrega
- mínimo, máximo, média e mediana da odd;
- abertura e odd mais recente;
- delta absoluto e percentual;
- direção e tendência por hora;
- velocidade média de alteração;
- volatilidade estatística;
- z-score da última odd e detecção de anomalia;
- visão agregada por evento/mercado;
- persistência histórica em `temporal_market_stats`;
- exportação para `data/opportunities/temporal_intelligence.json`.

## Execução
```powershell
python run_temporal.py
```

Personalizado:
```powershell
python run_temporal.py --hours 120 --windows 24 48 72 96 120
```

Importante: 24/48/72/96/120h são janelas históricas. Elas não relaxam o frescor do motor de Surebet, que continua usando os limites configurados no BLOCO 5/6.
