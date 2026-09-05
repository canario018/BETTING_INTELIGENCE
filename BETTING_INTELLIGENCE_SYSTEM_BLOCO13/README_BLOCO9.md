# BLOCO 9 — Opportunity Ranking + Intelligence Center

Transforma os sinais do BLOCO 8 em um ranking único de prioridade e em um dataset pronto para o Intelligence Center.

## Componentes
- `app/intelligence_center.py`: score composto, ranking, agregações por esporte/mercado e exportação.
- `app/intelligence_persistence.py`: histórico SQLite em `opportunity_rankings`.
- `run_intelligence_center.py`: execução operacional.

## Score
Combina, com limites para impedir que uma métrica domine:
- força do sinal;
- confiança;
- confiabilidade derivada;
- frescor;
- divergência entre casas;
- edge de Surebet com contribuição limitada;
- bônus pequeno para anomalia.

`SUREBET` recebe uma regra de piso para não ficar atrás de sinais puramente temporais quando a arbitragem atual foi confirmada.

## Importante
O ranking não é probabilidade de acerto nem recomendação automática. É uma fila de investigação/priorização baseada nos dados observados.
