# EXECUTAR BLOCO 12

## 1. Ambiente

Na raiz do projeto:

```bash
pip install -r requirements.txt
```

## 2. `.env`

Mantenha as casas desejadas em `COLLECTORS`.

Exemplo:

```env
COLLECTORS=estrelabet,lotogreen,multibet,apostaganha,betano
DATABASE_URL=sqlite:///./data/betting.db
BANKROLL=1000
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Não coloque token do Telegram no código-fonte.

## 3. Verificar saúde das APIs/collectors

```bash
python run_collector_health.py
```

Saída esperada:

```text
EstrelaBet      OK       3000 records ...
Lotogreen       OK       2800 records ...
...
```

`ERROR` significa que o collector não conseguiu obter/normalizar dados nesta execução.

## 4. Executar uma coleta real

```bash
python main.py
```

Depois abra `data/betting.db` no DB Browser for SQLite.

## 5. Calcular Value Bets

```bash
python run_value.py
```

O comando procura mercados completos suportados, com pelo menos duas casas, e aplica:

```text
odd → probabilidade implícita → de-vig → fair probability → fair odd → edge → EV
```

## 6. Monitor contínuo

```bash
python run_monitor.py --interval 60
```

Com alertas Telegram:

```bash
python run_monitor.py --interval 60 --alerts
```

## 7. Teste Telegram

Configure `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` no `.env`.

Primeiro:

```bash
python run_alerts.py --dry-run
```

Depois:

```bash
python run_alerts.py
```

## 8. Consultas no DB Browser

Tabelas novas:

```sql
SELECT * FROM value_opportunities ORDER BY expected_value_percent DESC;
```

```sql
SELECT * FROM value_observations ORDER BY observed_at DESC;
```

```sql
SELECT bookmaker, status, http_status, records_count, latency_ms, checked_at
FROM collector_health
ORDER BY checked_at DESC;
```

```sql
SELECT * FROM monitor_runs ORDER BY started_at DESC;
```

## 9. Interpretação

- **SUREBET** = arbitragem matemática entre casas.
- **VALUE_BET** = odd acima da fair odd estimada pelo consenso de mercado neste bloco.
- **STRONG_UP/DOWN / ANOMALY / DIVERGENCE** = sinais de movimento/estrutura do mercado.

Value Bet não é garantia de lucro. O próximo estágio é criar probabilidade independente, backtest e CLV.
