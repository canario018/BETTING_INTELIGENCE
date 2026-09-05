from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from app.collectors.registry import build_collectors

@dataclass
class CollectorHealthResult:
    bookmaker: str
    status: str
    latency_ms: float
    records: int
    http_status: int | None
    error: str | None
    endpoint: str

def check_collectors(settings):
    results=[]
    for c in build_collectors(settings):
        import time
        t=time.perf_counter()
        try:
            raw=c.fetch_raw_data(); records=c.normalize_data(raw)
            results.append(CollectorHealthResult(c.sportsbook_name,"OK",(time.perf_counter()-t)*1000,len(records),200,None,getattr(c,'api_endpoint','')))
        except Exception as exc:
            results.append(CollectorHealthResult(c.sportsbook_name,"ERROR",(time.perf_counter()-t)*1000,0,None,str(exc),getattr(c,'api_endpoint','')))
    return results
