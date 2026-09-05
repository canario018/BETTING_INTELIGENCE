# EXECUTAR BLOCO 4

## 1. Ativar ambiente
```powershell
.\.venv\Scripts\Activate.ps1
```

## 2. Testar
```powershell
python -m pytest -q
```

## 3. Coletar odds reais
```powershell
python main.py
```

## 4. Gerar oportunidades
```powershell
python run_opportunities.py --hours 24 --min-profit 0.10 --bankroll 1000
```

## 5. Abrir dataset para o dashboard
`data/opportunities/dashboard_opportunities.json`

## 6. Diagnóstico com filtros mais flexíveis
```powershell
python run_opportunities.py --hours 24 --min-profit 0.10 --bankroll 1000 --max-age-seconds 600 --max-spread-seconds 120
```

O modo flexível é para diagnóstico. Para uso operacional, mantenha os filtros de frescor mais rígidos.
