# Correção de Timeout — BLOCO 13

## Correção aplicada

O `run_collector_health.py` agora trata falhas individualmente por casa de aposta.

Se uma API apresentar timeout, erro HTTP, falha de JSON ou outra exceção:

- a casa recebe `STATUS=ERROR`;
- o tipo e a mensagem do erro são registrados;
- o diagnóstico continua para as demais casas;
- o programa não é encerrado por causa de uma única fonte indisponível.

Também foi corrigida a leitura das métricas retornadas por `assess_records()`,
que no BLOCO 13 são fornecidas como dicionário.

## Estados

- `OK`: resposta válida e odds normalizadas.
- `EMPTY`: resposta válida, mas nenhuma odd foi normalizada.
- `ERROR`: a requisição/processamento falhou.

## Teste recomendado

```powershell
python -m compileall -q app main.py run_value.py run_collector_health.py run_monitor.py run_alerts.py
python run_collector_health.py
```

Um timeout de uma casa não deve mais interromper o diagnóstico das demais.
