from __future__ import annotations
import argparse
from app.utils.logging_config import setup_logging
from app.monitor.runner import run_forever

def main():
    p=argparse.ArgumentParser(description="BLOCO 10 — Live Market Monitor + Continuous Scanning Engine")
    p.add_argument("--interval", type=int, default=60, help="segundos entre ciclos")
    p.add_argument("--cycles", type=int, default=0, help="0 = contínuo; use 1 para teste")
    p.add_argument("--no-signals", action="store_true")
    p.add_argument("--min-strength", type=float, default=40.0)
    p.add_argument("--bankroll", type=float, default=1000.0)
    p.add_argument("--change-threshold-percent", type=float, default=0.01)
    p.add_argument("--change-threshold-absolute", type=float, default=0.001)
    p.add_argument("--output", default="data/opportunities/live_monitor_status.json")
    p.add_argument("--alerts", action="store_true", help="ativa o Smart Alert Engine do BLOCO 11 a cada ciclo")
    p.add_argument("--alert-cooldown", type=int, default=300)
    p.add_argument("--alert-change-min-percent", type=float, default=1.0)
    p.add_argument("--alert-max-deliveries", type=int, default=10)
    p.add_argument("--alert-dry-run", action="store_true")
    a=p.parse_args(); setup_logging()
    run_forever(interval_seconds=a.interval, max_cycles=None if a.cycles<=0 else a.cycles, run_signals=not a.no_signals, min_strength=a.min_strength, bankroll=a.bankroll, output=a.output, threshold_percent=a.change_threshold_percent, threshold_absolute=a.change_threshold_absolute, run_alerts=a.alerts, alert_cooldown=a.alert_cooldown, alert_change_min_percent=a.alert_change_min_percent, alert_max_deliveries=a.alert_max_deliveries, alert_dry_run=a.alert_dry_run)
if __name__=="__main__": main()
