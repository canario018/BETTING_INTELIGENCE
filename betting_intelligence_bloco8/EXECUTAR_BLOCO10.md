# EXECUTAR BLOCO 10

## 1. Instalar dependências
```powershell
pip install -r requirements.txt
```

## 2. Conferir `.env`
Exemplo:
```env
COLLECTORS=estrelabet,lotogreen,multibet
REQUEST_TIMEOUT_SECONDS=15
IDEMPOTENCY_WINDOW_SECONDS=60
```

## 3. Rodar teste de integração de um ciclo
```powershell
python run_monitor.py --cycles 1 --interval 5
```

## 4. Verificar testes
```powershell
python -m pytest -q
```
Esperado no pacote: **37 passed** (5 warnings legados sobre `datetime.utcnow()`).

## 5. Iniciar monitor contínuo
```powershell
python run_monitor.py --interval 60
```

A cada ciclo o terminal informa o resultado; `Ctrl+C` encerra o processo.

## 6. Próximo passo
O BLOCO 11 deve consumir `market_changes` e aplicar **event deduplication, cooldown, severity e Telegram**, evitando spam e notificando somente mudanças realmente relevantes.
