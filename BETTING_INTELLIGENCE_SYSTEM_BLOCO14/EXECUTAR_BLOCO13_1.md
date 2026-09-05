# EXECUTAR BLOCO 13.1

## 1. Substituir o projeto

Preserve o seu `data/betting.db` e o `.env` atual. Extraia o ZIP em uma pasta limpa ou substitua os arquivos do projeto BLOCO 13.1.

## 2. Conferir `.env`

```env
COLLECTORS=estrelabet,lotogreen,multibet,onabet,r7bet,betbet,vbet,7kbet
REQUEST_TIMEOUT_SECONDS=15
SAVE_RAW_JSON=true
```

## 3. Validar

```powershell
python -m compileall -q app main.py run_value.py run_collector_health.py run_monitor.py run_alerts.py inspect_raw_payload.py
pytest -q
```

## 4. Rodar diagnóstico

```powershell
python run_collector_health.py
```

Agora, mesmo uma casa `EMPTY` com HTTP 200 terá seu payload preservado em `data/raw/<bookmaker>_latest.json`.

## 5. Inspecionar R7Bet

```powershell
python inspect_raw_payload.py data/raw/r7bet_latest.json --depth 3
```

## 6. Inspecionar Bet.Bet

```powershell
python inspect_raw_payload.py data/raw/bet_bet_latest.json --depth 3
```

## 7. Inspecionar VBET

```powershell
python inspect_raw_payload.py data/raw/vbet_latest.json --depth 4
```

> O nome do arquivo é derivado do nome da casa. Se o terminal do health mostrar outro caminho em `raw_file`, use exatamente aquele caminho.

## 8. 7KBet

Se continuar `HTTP=403`, não haverá RAW útil para parser porque o servidor recusou a requisição. A fonte deve ser tratada separadamente.
