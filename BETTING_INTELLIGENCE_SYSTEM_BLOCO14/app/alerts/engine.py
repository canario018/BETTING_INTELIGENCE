from __future__ import annotations
import hashlib, json
from datetime import datetime, timedelta, timezone
from app.analytics.arbitrage import analyze_database
from app.alerts.models import AlertEventModel, AlertDeliveryModel


def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def _clip(v, lo=0.0, hi=100.0): return max(lo, min(hi, float(v)))
def _hash(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

def severity_for(alert_type, score, profit=0.0):
    if alert_type == "SUREBET" and profit >= 1.0: return "CRITICAL"
    if score >= 85: return "CRITICAL"
    if score >= 70: return "HIGH"
    if score >= 50: return "MEDIUM"
    return "LOW"

def _money(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_surebet(sb):
    lines = ["🚨 SUREBET DETECTADA", "", f"⚽ {sb.home_team} x {sb.away_team}", f"Mercado: {sb.market_type}" + (f" | Linha: {sb.line}" if sb.line is not None else ""), ""]
    stakes = sb.stakes()
    for i, leg in enumerate(sb.legs, 1):
        lines.append(f"{i}. {leg.bookmaker} — {leg.selection_code} @ {leg.odd:.4f} — Stake: {_money(stakes.get(leg.selection_code, 0.0))}")
    lines += ["", f"ROI garantido: {sb.profit_percent:.3f}%", f"Retorno analítico: {_money(sb.guaranteed_return)}", f"Lucro analítico: {_money(sb.guaranteed_profit)}", f"Casas: {sb.bookmaker_count}", f"Freshness: {sb.max_age_seconds:.0f}s | spread: {sb.timestamp_spread_seconds:.0f}s", "", "⚠️ Alerta analítico. Nenhuma aposta é executada automaticamente."]
    return "\n".join(lines)

def build_surebet_alerts(db, bankroll=1000.0, max_age_seconds=180, max_timestamp_spread_seconds=30, min_profit_percent=0.0):
    surebets = analyze_database(db, lookback_hours=1, min_profit_percent=min_profit_percent, max_age_seconds=max_age_seconds, max_timestamp_spread_seconds=max_timestamp_spread_seconds, distinct_bookmakers=True, bankroll=bankroll)
    out=[]
    for sb in surebets:
        leg_sig="|".join(f"{x.bookmaker}:{x.selection_code}:{x.odd:.6f}" for x in sb.legs)
        alert_key=f"SUREBET|{sb.event_key}|{sb.market_type}|{sb.line}|{leg_sig}"
        score=_clip(80 + sb.profit_percent*10 + min(10, sb.bookmaker_count*2) - min(10, sb.max_age_seconds/30))
        out.append({"alert_key":alert_key,"event_key":sb.event_key,"alert_type":"SUREBET","severity":severity_for("SUREBET",score,sb.profit_percent),"score":round(score,2),"title":"SUREBET DETECTADA","message":format_surebet(sb),"payload":{"event_key":sb.event_key,"market_type":sb.market_type,"line":sb.line,"profit_percent":sb.profit_percent,"bankroll":bankroll,"legs":[vars(x) for x in sb.legs]}})
    return out

def should_suppress(db, alert_key, cooldown_seconds=300):
    cutoff=utcnow_naive()-timedelta(seconds=cooldown_seconds)
    recent=db.query(AlertEventModel).filter(AlertEventModel.alert_key==alert_key, AlertEventModel.created_at>=cutoff, AlertEventModel.status.in_(["SENT","PENDING","SUPPRESSED"])).first()
    return recent is not None

def persist_alert_candidates(db, candidates, cooldown_seconds=300):
    created=[]
    for c in candidates:
        if should_suppress(db,c["alert_key"],cooldown_seconds):
            continue
        now=utcnow_naive(); dedupe=_hash(c["alert_key"])
        row=AlertEventModel(created_at=now,event_key=c["event_key"],alert_key=c["alert_key"],alert_type=c["alert_type"],severity=c["severity"],score=c["score"],title=c["title"],message=c["message"],payload_json=json.dumps(c.get("payload",{}),ensure_ascii=False),dedupe_hash=dedupe,status="PENDING")
        db.add(row); created.append(row)
    db.commit(); return created

def deliver_pending(db, sender, max_alerts=10):
    rows=db.query(AlertEventModel).filter(AlertEventModel.status=="PENDING").order_by(AlertEventModel.score.desc(), AlertEventModel.created_at.asc()).limit(max_alerts).all()
    results=[]
    for row in rows:
        now=utcnow_naive()
        try:
            data=sender.send_message(row.message)
            msg_id=str(data.get("result",{}).get("message_id",""))
            row.status="SENT"; row.sent_at=now
            db.add(AlertDeliveryModel(alert_event_id=row.id,attempted_at=now,channel="TELEGRAM",status="SENT",response_code=200,message_id=msg_id))
            results.append((row.id,"SENT"))
        except Exception as exc:
            row.status="ERROR"
            db.add(AlertDeliveryModel(alert_event_id=row.id,attempted_at=now,channel="TELEGRAM",status="ERROR",error_message=str(exc)[:2000]))
            results.append((row.id,"ERROR"))
    db.commit(); return results
