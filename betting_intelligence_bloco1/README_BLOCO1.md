# BLOCO 1 — Coletores Reais + Normalização + SQLite

Esta versão consolida o primeiro fluxo vertical do projeto.

## O que foi implementado

- Um coletor genérico para a estrutura Altenar `GetCouponEvents`.
- Integrações oficiais do projeto para EstrelaBet, Lotogreen e Multibet, usando as integrações/endpoints que já aparecem nos arquivos de captura deste projeto.
- Relação `events -> marketIds -> markets -> oddIds -> odds`.
- Relação auxiliar `sports`, `champs` e `competitors`.
- Normalização para o contrato `OddPayload`.
- Normalização de mercados principais: MATCH_RESULT, DOUBLE_CHANCE, DRAW_NO_BET, TOTAL_GOALS e BOTH_TEAMS_TO_SCORE.
- Normalização das seleções: HOME, DRAW, AWAY, OVER, UNDER, YES, NO e combinações de dupla chance.
- Extração da linha a partir de nomes como `Mais de 2.5`.
- Validação de odd > 1.0.
- Persistência em `odds_snapshots`.
- Idempotência configurável por `IDEMPOTENCY_WINDOW_SECONDS`.
- Pipeline paralelo no `main.py`.
- Testes com os três JSONs reais já presentes no projeto.

## Validação realizada

Os payloads locais foram processados antes do empacotamento:

- EstrelaBet: 9 eventos / 104 odds normalizadas.
- Lotogreen: 8 eventos / 107 odds normalizadas.
- Multibet: 8 eventos / 107 odds normalizadas.
- Total: 318 snapshots gravados em SQLite de teste.

Comando:

```powershell
python validate_block1.py
```

## Rodar coleta real

1. Ative a `.venv`.
2. Instale dependências:

```powershell
pip install -r requirements.txt
```

3. Confira o `.env`:

```text
COLLECTORS=estrelabet,lotogreen,multibet
```

4. Execute:

```powershell
python main.py
```

O terminal deve informar a quantidade de odds normalizadas por casa e quantos snapshots foram gravados.

## Importante

Os arquivos `extrator_*.py` continuam no projeto como ferramentas de investigação/debug. O fluxo oficial agora passa por `app/collectors/`.

Superbet, Novibet e Betano não foram falsamente marcadas como prontas. Só devem entrar no `.env` quando o endpoint/estrutura real estiver confirmado.

Não há automação de login, CAPTCHA bypass, apostas ou contorno de bloqueios.

## Próximo bloco

Depois que `python main.py` estiver gravando dados reais, o próximo passo é o **BLOCO 2 — Market Normalizer + Event Matching + Surebet Engine 2.0**.
