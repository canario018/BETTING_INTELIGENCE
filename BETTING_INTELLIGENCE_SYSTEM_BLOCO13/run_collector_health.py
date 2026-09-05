from app.config.settings import settings
from app.diagnostics.health import check_collectors

print("=" * 125)
print("BETTING INTELLIGENCE SYSTEM - HEALTH / QUALIDADE / DIAGNÓSTICO DOS COLETORES")
print("=" * 125)

results = check_collectors(settings)

for x in results:
    print(
        f"{x.bookmaker:12} {x.status:6} HTTP={str(x.http_status):>3} "
        f"records={x.records:5} eventos={x.unique_events:4} "
        f"quality={x.quality_score:6.1f} "
        f"dup={x.duplicate_rate_percent:5.1f}% "
        f"sem_inicio={x.missing_start_percent:5.1f}% "
        f"markets={x.supported_market_percent:5.1f}% "
        f"lat={x.latency_ms:8.1f}ms"
    )
    print(f"  endpoint: {x.endpoint}")
    print(f"  bytes: {x.response_bytes}")
    print(f"  raw_saved: {x.raw_saved}  file: {x.raw_file}")
    print(f"  payload: {x.payload_type or '-'} | {x.payload_summary or '-'}")
    if x.payload_top_keys:
        print(f"  top_keys: {x.payload_top_keys}")
    if x.payload_sha256:
        print(f"  sha256: {x.payload_sha256}")
    if x.error:
        print(f"  ERROR: {x.error}")

print("-" * 125)
print("RESUMO")
print(f"OK={sum(x.status == 'OK' for x in results)} | EMPTY={sum(x.status == 'EMPTY' for x in results)} | ERROR={sum(x.status == 'ERROR' for x in results)} | TOTAL={len(results)}")
print(f"RAW directory: {settings.raw_data_dir}")
print("EMPTY = API respondeu, mas o parser não normalizou odds. ERROR = falha HTTP/rede/JSON/outro. Não há bypass de proteção.")
