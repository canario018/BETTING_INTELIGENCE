# BLOCO 11 — EVENT QUEUE + SMART TELEGRAM ALERT ENGINE

O BLOCO 11 transforma a fila `market_changes` em alertas analíticos inteligentes.

## Arquitetura
```text
market_changes + Surebets
        ↓
Alert Candidate Engine
        ↓
Deduplicação + Cooldown
        ↓
Severity / Score
        ↓
alert_events
        ↓
Telegram Delivery
        ↓
alert_deliveries
```

## Segurança
- Nenhuma aposta é executada.
- Não há login, CAPTCHA bypass, anti-bot ou alteração de conta.
- Telegram é somente canal de notificação.
- Sem token/chat id o sistema opera em DRY-RUN.

## Configuração
No `.env`:
```env
TELEGRAM_BOT_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
```
Nunca publique o token no código ou no repositório.

## Teste seguro
```powershell
python run_alerts.py --dry-run
```

## Produção de alertas Telegram
```powershell
python run_alerts.py --cooldown 300 --max-deliveries 10
```

## Sensibilidade
```powershell
python run_alerts.py --change-min-percent 1.0 --cooldown 300
```

### Tipos
- `SUREBET`: matemática de arbitragem válida sob os filtros atuais.
- `MARKET_CHANGE`: movimento relevante da odd.

### Cooldown
A mesma chave lógica não gera novo alerta durante a janela configurada. Mudança para uma nova configuração de odd pode gerar novo evento.

### Histórico
`alert_events` guarda candidatos, status, score, severidade e payload.
`alert_deliveries` guarda cada tentativa de entrega.
