# EXECUTAR BLOCO 13

## 1. Atualizar o projeto

Substitua os arquivos do projeto pelo conteúdo deste BLOCO 13, preservando `data/betting.db`.

Não apague o banco.

## 2. Instalar dependências

```powershell
pip install -r requirements.txt
```

## 3. Configurar `.env`

Comece com:

```env
COLLECTORS=estrelabet,lotogreen,multibet,onabet,r7bet,betbet,vbet,7kbet
REQUEST_TIMEOUT_SECONDS=15
SAVE_RAW_JSON=true
```

## 4. Validar sintaxe

```powershell
python -m compileall -q app main.py run_collector_health.py run_value.py run_monitor.py run_alerts.py
```

## 5. Inicializar schema

```powershell
python main.py
```

O BLOCO 12 corrigido mantém a ordem correta:

1. importa os models;
2. cria tabelas ausentes;
3. aplica migrações incrementais.

## 6. Diagnóstico individual das fontes

```powershell
python run_collector_health.py
```

Observe principalmente:

- `OK`;
- `EMPTY`;
- `ERROR`;
- HTTP;
- records;
- eventos;
- quality;
- latência.

## 7. Rodar a coleta completa

```powershell
python main.py
```

Os JSONs brutos serão salvos em:

```text
data/raw/
```

## 8. Value Bets

```powershell
python run_value.py
```

## 9. Monitoramento contínuo

```powershell
python run_monitor.py --interval 60
```

## 10. Se alguma fonte retornar EMPTY

Não altere o endpoint imediatamente.

Primeiro abra o JSON correspondente em:

```text
data/raw/
```

Exemplos:

```text
r7bet_latest.json
bet.bet_latest.json
vbet_latest.json
7kbet_latest.json
onabet_latest.json
```

O parser genérico foi criado de forma conservadora. O próximo ajuste deve ser feito com base na estrutura real recebida.

## 11. Segurança

Não há login automático, execução de apostas, bypass de CAPTCHA, bypass de autenticação ou contorno de restrições.
