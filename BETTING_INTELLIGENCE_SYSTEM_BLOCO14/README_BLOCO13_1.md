# BLOCO 13.1 — RAWs persistentes e diagnóstico aprofundado

O BLOCO 13.1 mantém toda a arquitetura do BLOCO 13 e corrige uma lacuna descoberta no health check: respostas HTTP 200 das novas APIs que resultavam em `EMPTY` não eram preservadas em `data/raw/`.

## O que mudou

- `run_collector_health.py` agora salva o RAW de cada collector que conseguiu obter uma resposta JSON, mesmo quando a normalização retorna zero registros.
- Arquivos são gravados como `data/raw/<bookmaker>_latest.json` usando escrita atômica.
- O diagnóstico mostra tipo do payload, resumo de listas no topo, chaves de topo, tamanho, SHA-256 e caminho do RAW.
- Falha de uma casa continua isolada: `ERROR` não interrompe as demais.
- `inspect_raw_payload.py` permite examinar a estrutura do JSON sem despejar megabytes no terminal.
- O `save_raw_json=true` do `.env` controla a persistência.

## Estados

- `OK`: resposta válida + odds normalizadas.
- `EMPTY`: resposta válida, mas parser não encontrou odds reconhecíveis. O RAW fica disponível para desenvolver o parser específico.
- `ERROR`: timeout, HTTP, JSON ou outra exceção.

## Próximo passo

Após `python run_collector_health.py`, use `inspect_raw_payload.py` nos `EMPTY`, principalmente R7Bet e Bet.Bet. O parser deve ser adaptado a partir do JSON real recebido; não se deve inventar caminhos de campos.

O projeto continua estritamente analítico: não há login automatizado, execução de apostas, bypass de CAPTCHA ou contorno de proteção de acesso.
