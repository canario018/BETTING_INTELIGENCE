from __future__ import annotations
import argparse, json
from app.config.settings import settings
from app.database.connection import SessionLocal, Base, engine
from app.database.migrations import ensure_schema, backfill_canonical_fields
from app.alerts.telegram import TelegramSender
from app.alerts.service import run_alert_cycle
from app.utils.logging_config import setup_logging

def main():
    p=argparse.ArgumentParser(description="BLOCO 11 — Event Queue + Smart Telegram Alert Engine")
    p.add_argument("--bankroll",type=float,default=settings.bankroll)
    p.add_argument("--min-profit",type=float,default=0.0)
    p.add_argument("--change-min-percent",type=float,default=1.0)
    p.add_argument("--cooldown",type=int,default=300)
    p.add_argument("--max-deliveries",type=int,default=10)
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args(); setup_logging(); ensure_schema(); Base.metadata.create_all(bind=engine)
    db=SessionLocal(); backfill_canonical_fields(db); db.close(); db=SessionLocal()
    try:
        sender=TelegramSender(settings.telegram_bot_token,settings.telegram_chat_id,settings.request_timeout_seconds) if settings.telegram_bot_token and settings.telegram_chat_id else None
        result=run_alert_cycle(db,sender,bankroll=a.bankroll,min_profit_percent=a.min_profit,change_min_delta_percent=a.change_min_percent,cooldown_seconds=a.cooldown,max_deliveries=a.max_deliveries,dry_run=a.dry_run or sender is None)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    finally: db.close()
if __name__=="__main__": main()
