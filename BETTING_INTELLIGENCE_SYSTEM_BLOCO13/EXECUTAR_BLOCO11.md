# EXECUTAR BLOCO 11

1. Rode a suíte:
```powershell
python -m pytest -q
```

2. Faça um teste sem Telegram:
```powershell
python run_alerts.py --dry-run
```

3. Configure no `.env`:
```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

4. Execute:
```powershell
python run_alerts.py
```

O engine envia somente alertas analíticos. Não executa apostas.
