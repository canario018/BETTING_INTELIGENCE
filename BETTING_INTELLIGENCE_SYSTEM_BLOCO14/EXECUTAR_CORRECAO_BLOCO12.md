# EXECUTAR A CORREÇÃO — BLOCO 12

## 1. Feche processos antigos

Se houver `python main.py` ou `run_monitor.py` rodando, interrompa com:

```text
Ctrl + C
```

## 2. Confirme a pasta

No terminal do VS Code:

```powershell
cd C:\Users\Arthur\Desktop\BETTING_INTELLIGENCE\BETTING_INTELLIGENCE_SYSTEM_BLOCO12
```

## 3. Confirme o arquivo corrigido

Abra:

```text
app/database/migrations.py
```

Ele NÃO deve conter:

```python
from app.intelligence_center import OpportunityRankingModel
```

O pacote corrigido usa o módulo correto:

```python
from app import intelligence_persistence
```

## 4. Valide a sintaxe

```powershell
python -m compileall -q app main.py run_value.py run_collector_health.py run_monitor.py run_alerts.py
```

## 5. Inicialize e faça a coleta real

```powershell
python main.py
```

## 6. Verifique a saúde dos coletores

```powershell
python run_collector_health.py
```

Observe principalmente:

- `status`;
- `http_status`;
- `records`;
- `latency_ms`;
- `response_bytes`;
- `error`.

## 7. Teste Value Bets

```powershell
python run_value.py
```

## 8. Teste o monitor

```powershell
python run_monitor.py --interval 60
```

## 9. Não habilite Telegram ainda

Primeiro confirme que coleta, banco, saúde e Value Bets estão funcionando. Depois teste:

```powershell
python run_monitor.py --interval 60 --alerts --alert-dry-run
```

## 10. Banco

O arquivo esperado é:

```text
data/betting.db
```

Não apague esse arquivo durante esta correção.
