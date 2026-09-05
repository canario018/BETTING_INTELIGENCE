# EXECUTAR BLOCO 6

## 1. Substituir o projeto
Use o conteúdo deste pacote como continuação do BLOCO 5.

## 2. Ambiente
```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Testes
```powershell
python -m pytest -q
```
Esperado: `23 passed`.

## 4. Coleta real
```powershell
python main.py
```
O `main.py` agora cria/migra as colunas canônicas e faz backfill de registros antigos antes da nova coleta.

## 5. Análise
```powershell
python run_opportunities.py --hours 24 --min-profit 0.10 --bankroll 1000
```

## 6. O que observar
Procure no banco:
- `event_start_at`
- `canonical_event_id`
- `canonical_sport`
- `canonical_market`
- `canonical_selection`

Para o mesmo jogo entre casas diferentes, o objetivo é que o `canonical_event_id` seja igual quando esporte, participantes e horário representarem o mesmo evento.

## 7. Importante
O matching é conservador. Se duas fontes apresentarem equipes invertidas, horários muito diferentes ou dados insuficientes para identificar o evento com segurança, o sistema prefere não cruzar as cotações.
