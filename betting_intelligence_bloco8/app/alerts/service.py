from __future__ import annotations
import json
from datetime import timedelta
from sqlalchemy import func
from app.alerts.models import AlertEventModel
from app.alerts.engine import utcnow_naive, persist_alert_candidates, deliver_pending
from app.monitor.models import MarketChangeModel

def change_candidates(db, min_delta_percent=1.0, cooldown_seconds=300, limit=100):
    cutoff=utcnow_naive()-timedelta(seconds=15*60)
    rows=db.query(MarketChangeModel).filter(MarketChangeModel.detected_at>=cutoff, MarketChangeModel.processed==False, func.abs(MarketChangeModel.delta_percent)>=min_delta_percent).order_by(MarketChangeModel.detected_at.desc()).limit(limit).all()
    candidates=[]
    for r in rows:
        score=min(100.0, 45 + abs(r.delta_percent)*4 + (10 if r.direction=="DOWN" else 0))
        severity="CRITICAL" if score>=85 else "HIGH" if score>=70 else "MEDIUM" if score>=50 else "LOW"
        alert_key=f"CHANGE|{r.change_key}|{r.direction}|{round(r.current_odd,6)}"
        message=(f"📈 MOVIMENTO DE MERCADO\n\n{r.event_key}\nMercado: {r.market_type}"
                 f"{(' | Linha: '+str(r.line)) if r.line is not None else ''}\n"
                 f"Casa: {r.bookmaker}\nSeleção: {r.selection_code}\n\n"
                 f"Odd: {r.previous_odd:.4f} → {r.current_odd:.4f}\n"
                 f"Variação: {r.delta_percent:+.2f}% ({r.direction})\n\n"
                 f"Prioridade: {severity}\n⚠️ Alerta analítico; nenhuma aposta é executada automaticamente.")
        candidates.append({"alert_key":alert_key,"event_key":r.event_key,"alert_type":"MARKET_CHANGE","severity":severity,"score":round(score,2),"title":"MOVIMENTO DE MERCADO","message":message,"payload":json.loads(r.payload_json or "{}")})
    return candidates, rows

def run_alert_cycle(db, sender=None, *, bankroll=1000.0, min_profit_percent=0.0, change_min_delta_percent=1.0, cooldown_seconds=300, max_deliveries=10, dry_run=False):
    from app.alerts.engine import build_surebet_alerts
    candidates=build_surebet_alerts(db,bankroll=bankroll,min_profit_percent=min_profit_percent)
    changes, rows=change_candidates(db,change_min_delta_percent,cooldown_seconds)
    candidates.extend(changes)
    created=persist_alert_candidates(db,candidates,cooldown_seconds)
    for r in rows: r.processed=True
    db.commit()
    deliveries=[]
    if sender is not None and not dry_run:
        deliveries=deliver_pending(db,sender,max_alerts=max_deliveries)
    elif dry_run:
        for row in created:
            row.status="DRY_RUN"
        db.commit()
    return {"candidates":len(candidates),"created":len(created),"deliveries":deliveries,"dry_run":dry_run}
