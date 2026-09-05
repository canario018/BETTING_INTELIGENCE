# EXECUTAR BLOCO 8

Abra o PowerShell na raiz do projeto.

## 1. Instalar dependências

```powershell
pip install -r requirements.txt
```

## 2. Testar

```powershell
python -m pytest -q
```

## 3. Rodar o Signal Engine

```powershell
python run_signals.py --hours 120 --windows 24 48 72 96 120 --min-strength 40 --bankroll 1000
```

## 4. Inspecionar

Arquivo:

```text
data/opportunities/market_signals.json
```

Tabela SQLite:

```text
market_signals
```

## 5. Interpretação

Priorize primeiro `SUREBET`, depois `STRONG_DOWN`/`STRONG_UP` e `ANOMALY`, sempre conferindo o histórico e a idade real dos snapshots. O score não é garantia de resultado.
