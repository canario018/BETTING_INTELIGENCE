# BLOCO 2 — Odds reais no SQLite + Surebet Engine

## Objetivo

Fechar o fluxo real do projeto:

API pública conhecida → collector → normalização → validação → SQLite → análise de surebet.

## Casas Altenar configuradas

- EstrelaBet (`integration=estrelabet`)
- Lotogreen (`integration=lotogreen`)
- Multibet (`integration=multibet.br`)

Os scripts `extrator_*.py` continuam como ferramentas de investigação/debug. O fluxo oficial usa `app/collectors/`.

## 1. Instalação

No PowerShell, dentro do projeto:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Testar com os JSONs reais já capturados

```powershell
python -m pytest -q
```

Esse teste confirma que os payloads reais usados no projeto são convertidos para o contrato que alimenta o SQLite.

## 3. Coleta online real

```powershell
python main.py
```

O programa consulta os endpoints configurados, normaliza as odds e grava snapshots em:

```text
data/betting.db
```

Os payloads brutos mais recentes são preservados em:

```text
data/raw/
```

Se uma casa falhar, o programa registra o erro e não inventa dados.

## 4. Conferir o SQLite

```powershell
python inspect_db.py
```

Você deve encontrar registros com bookmaker, evento, mercado, seleção e odd.

## 5. Rodar o motor de surebet

```powershell
python run_analysis.py
```

A fórmula principal é:

```text
S = 1/Odd1 + 1/Odd2 + ... + 1/OddN
```

Existe surebet quando:

```text
S < 1
```

E o ROI teórico é:

```text
ROI = (1/S - 1) × 100
```

O algoritmo exige todas as saídas do universo conhecido do mercado (por exemplo, HOME/DRAW/AWAY no 1X2) e evita usar a mesma bookmaker em duas pernas.

## Importante

O motor é matemático. Antes de considerar uma oportunidade executável, é necessário confirmar manualmente que os mercados são realmente equivalentes: período, linha, regras de liquidação, status da odd e disponibilidade.

O sistema não realiza apostas, login, bypass de CAPTCHA ou contorno de restrições.
