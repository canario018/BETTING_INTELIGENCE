# BLOCO 4 — Opportunity Center

Esta camada transforma o Surebet Engine em um centro de oportunidades.

## Componentes
- `app/opportunities/models.py`: histórico persistente de oportunidades e alertas.
- `app/opportunities/service.py`: score, fingerprint, movimentação, persistência, expiração e dataset do dashboard.
- `run_opportunities.py`: pipeline completo.
- `app/dashboard/export.py`: exportação independente do dataset visual.

## Score de confiabilidade
O score (0–100) combina margem de ROI, frescor, sincronização temporal e quantidade de casas. É um score operacional e não uma garantia de lucro.

## Movimentação
O sistema preserva snapshots das odds no SQLite e calcula abertura, última odd, delta, variação percentual e quantidade de amostras por casa/seleção.

## Alertas
São registrados localmente em SQLite. Não há envio automático, login, execução de aposta ou contorno de restrições.

## Dashboard
O arquivo `data/opportunities/dashboard_opportunities.json` é uma camada de consumo preparada para Power BI, Streamlit, web app ou outro front-end.
