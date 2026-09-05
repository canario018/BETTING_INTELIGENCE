from app.config.settings import settings
from app.diagnostics.health import check_collectors
for x in check_collectors(settings):
    print(f"{x.bookmaker:15} {x.status:7} {x.records:6} records {x.latency_ms:8.1f} ms | {x.endpoint}")
    if x.error: print('  ERROR:', x.error)
