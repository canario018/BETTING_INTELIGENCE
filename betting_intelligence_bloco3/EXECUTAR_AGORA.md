# EXECUTE AGORA — BLOCO 2

## 1. Abra o PowerShell na pasta do projeto

```powershell
cd C:\caminho\para\betting_intelligence
.\.venv\Scripts\Activate.ps1
```

## 2. Instale/atualize as dependências

```powershell
pip install -r requirements.txt
```

## 3. Confirme os coletores

No `.env`:

```text
COLLECTORS=estrelabet,lotogreen,multibet
```

## 4. Rode a coleta REAL

```powershell
python main.py
```

Procure no terminal por algo semelhante a:

```text
EstrelaBet: XXX odds normalizadas
Lotogreen: XXX odds normalizadas
Multibet: XXX odds normalizadas
Novos snapshots salvos: XXX
Banco: sqlite:///./data/betting.db
Coleta real concluída.
```

O número não precisa ser exatamente igual ao exemplo. O importante é ser > 0 e não haver erro no collector.

## 5. Confira o banco

```powershell
python inspect_db.py
```

Isso deve mostrar bookmaker, evento, mercado, seleção e odd.

## 6. Abra no DB Browser for SQLite

Abra:

```text
data\betting.db
```

Depois:

1. Aba **Browse Data**
2. Tabela `odds_snapshots`
3. Confira `bookmaker`
4. Confira `home_team` e `away_team`
5. Confira `market_type`
6. Confira `selection_code`
7. Confira `odd`
8. Confira `collected_at`

## 7. Rode o Surebet Engine

```powershell
python run_analysis.py
```

Se aparecer:

```text
Surebets encontradas: 0
```

isso NÃO significa erro. Significa apenas que, na janela analisada, nenhuma combinação válida teve:

```text
Σ(1 / odd) < 1
```

## 8. Forçar uma janela maior

```powershell
python run_analysis.py --hours 48
```

## 9. Aceitar somente oportunidades acima de determinado ROI

Exemplo de 1%:

```powershell
python run_analysis.py --min-profit 1
```

## 10. Definir a banca para cálculo de stake

```powershell
python run_analysis.py --bankroll 1000
```

O programa calcula a divisão proporcional da banca, mas NÃO realiza apostas.

---

# FLUXO FINAL DESTA ETAPA

```text
API pública conhecida
        ↓
EstrelaBet / Lotogreen / Multibet
        ↓
AltenarCouponCollector
        ↓
NORMALIZAÇÃO
        ↓
OddPayload (Pydantic)
        ↓
OddsRepository
        ↓
SQLite
        ↓
inspect_db.py
        ↓
Surebet Engine
        ↓
Σ(1/odd)
        ↓
ROI
        ↓
Stake Calculator
```

## BLOCO 3 — Motor profissional

Depois da coleta real, execute:

```powershell
python -m pytest -q
python run_analysis.py
```

Filtros padrão do motor profissional:
- odd com até 180 segundos;
- diferença máxima de 30 segundos entre as pernas;
- uma bookmaker por perna;
- mercado completo;
- somente `MATCH_RESULT`, `TOTAL_GOALS` e `BOTH_TEAMS_TO_SCORE`.

Exemplo para ampliar a janela operacional:

```powershell
python run_analysis.py --hours 24 --min-profit 0.10 --bankroll 1000 --max-age-seconds 600 --max-spread-seconds 120
```
