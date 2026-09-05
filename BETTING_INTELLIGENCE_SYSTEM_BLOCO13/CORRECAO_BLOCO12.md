# CORREÇÃO DO BLOCO 12 — Inicialização do banco e migrações

## Problema identificado

O erro:

```text
sqlite3.OperationalError: no such table: monitor_runs
```

ocorre quando o código tenta executar `ALTER TABLE monitor_runs` antes de a tabela existir.

Durante a correção manual também pode aparecer:

```text
ImportError: cannot import name 'OpportunityRankingModel' from 'app.intelligence_center'
```

Esse import é incorreto. `OpportunityRankingModel` pertence ao módulo `app.intelligence_persistence`, e não ao `app.intelligence_center`.

## Correção aplicada neste pacote

O `app/database/migrations.py` foi reorganizado para:

1. registrar todos os módulos que possuem modelos SQLAlchemy;
2. executar `Base.metadata.create_all(bind=engine)` primeiro;
3. somente depois adicionar colunas ausentes com `ALTER TABLE`;
4. nunca tentar alterar `monitor_runs`, `collector_health` ou `odds_snapshots` antes da criação da tabela;
5. manter o banco existente e não apagar `data/betting.db`.

## Procedimento no Windows / VS Code

Abra o terminal na pasta do projeto:

```powershell
cd C:\Users\Arthur\Desktop\BETTING_INTELLIGENCE\BETTING_INTELLIGENCE_SYSTEM_BLOCO12
```

Atualize o código do pacote corrigido nessa pasta, preservando seu `.env` e seu `data/betting.db`.

Depois execute, nesta ordem:

```powershell
python -m compileall -q app main.py run_value.py run_collector_health.py run_monitor.py run_alerts.py
```

Se não houver erro:

```powershell
python main.py
```

Depois:

```powershell
python run_collector_health.py
```

Depois:

```powershell
python run_value.py
```

E somente então:

```powershell
python run_monitor.py --interval 60
```

## Regra importante

Não apague `data/betting.db` para corrigir esse erro. A intenção desta migração é preservar o histórico já coletado pelos blocos anteriores.

Se surgir outro traceback, pare nesse ponto e use o traceback completo para a próxima correção.
