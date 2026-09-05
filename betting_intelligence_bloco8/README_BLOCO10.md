# BLOCO 10 — LIVE MARKET MONITOR + CONTINUOUS SCANNING ENGINE

O BLOCO 10 transforma o projeto de execução manual em um **motor contínuo de monitoramento analítico**.

## Fluxo

```text
Collectors em paralelo
        ↓
Normalização + canonicalização
        ↓
Snapshot no SQLite
        ↓
Change Detection
        ↓
Market Change Queue
        ↓
Signal Engine
        ↓
Opportunity Ranking
        ↓
Intelligence Center
        ↓
próximo ciclo
```

## Novas tabelas

- `monitor_runs`: histórico de cada ciclo, duração, volume, erros e resultados.
- `collector_health`: saúde individual de cada bookmaker por ciclo.
- `market_changes`: fila histórica de alterações de mercado, com odd anterior, atual, delta, direção e status `processed`.

## Conceitos importantes

### Ciclo
Cada ciclo dispara todos os collectors configurados em paralelo. Um erro de uma casa não interrompe as demais; o ciclo fica `PARTIAL`.

### Intervalo
O padrão é 60 segundos. O motor pode ficar contínuo (`--cycles 0`) ou ser executado por uma quantidade limitada para teste.

### Change Detection
A comparação utiliza a identidade canônica do projeto:
`canonical_event_id + canonical_market + line + bookmaker + canonical_selection`.

Mudanças menores que os dois thresholds configurados são ignoradas.

### Event queue
`market_changes` é a fila analítica. O BLOCO 10 não envia Telegram e não executa apostas. O BLOCO 11 poderá consumir somente eventos relevantes dessa fila para notificações.

## Comandos

### Teste de 1 ciclo
```powershell
python run_monitor.py --cycles 1 --interval 5
```

### Monitor contínuo
```powershell
python run_monitor.py --interval 60
```

### Monitor sem recalcular sinais/ranking
```powershell
python run_monitor.py --interval 60 --no-signals
```

### Ajustar sensibilidade
```powershell
python run_monitor.py --interval 60 --change-threshold-percent 0.05 --change-threshold-absolute 0.01
```

## Saídas

- `data/opportunities/live_monitor_status.json`
- `data/opportunities/market_signals.json`
- `data/opportunities/intelligence_center.json`
- banco SQLite com snapshots, mudanças, saúde dos collectors, sinais e rankings.

## Operação segura

O monitor é exclusivamente analítico. Não há login, CAPTCHA bypass, anti-bot evasion, clique, execução de aposta ou alteração de conta.
