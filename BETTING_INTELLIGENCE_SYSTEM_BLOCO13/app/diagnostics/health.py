from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any
import time

from app.collectors.registry import build_collectors
from app.diagnostics.quality import assess_records


@dataclass
class CollectorHealthResult:
    bookmaker: str
    status: str
    latency_ms: float
    records: int
    http_status: int | None
    error: str | None
    endpoint: str
    response_bytes: int | None = None
    quality_score: float = 0.0
    unique_events: int = 0
    duplicate_rate_percent: float = 0.0
    missing_start_percent: float = 0.0
    supported_market_percent: float = 0.0
    raw_saved: bool = False
    raw_file: str | None = None
    payload_type: str | None = None
    payload_sha256: str | None = None
    payload_top_keys: str | None = None
    payload_summary: str | None = None


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "collector"


def _json_default(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _payload_shape(raw: Any) -> tuple[str, str, str | None]:
    """Retorna tipo, resumo simples e chaves de topo sem despejar o JSON inteiro."""
    if isinstance(raw, dict):
        keys = list(raw.keys())
        preview = ", ".join(str(k) for k in keys[:20])
        lengths = []
        for key, value in raw.items():
            if isinstance(value, list):
                lengths.append(f"{key}[{len(value)}]")
        summary = "object"
        if lengths:
            summary += " | " + ", ".join(lengths[:12])
        return "object", summary, preview
    if isinstance(raw, list):
        child_types = sorted({type(x).__name__ for x in raw[:50]})
        return "array", f"array[{len(raw)}] tipos={','.join(child_types) or 'vazio'}", None
    if raw is None:
        return "null", "null", None
    return type(raw).__name__, str(raw)[:200], None


def save_raw_payload(raw: Any, output_dir: str | Path, bookmaker: str) -> tuple[bool, str | None, str | None, str | None, str | None, str | None]:
    """Salva sempre o payload recebido pelo health check, inclusive quando o parser retorna EMPTY."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    slug = _safe_slug(bookmaker)
    target = directory / f"{slug}_latest.json"
    tmp = directory / f".{slug}_latest.json.tmp"
    try:
        serialized = json.dumps(raw, ensure_ascii=False, indent=2, default=_json_default)
        tmp.write_text(serialized, encoding="utf-8")
        tmp.replace(target)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        payload_type, summary, top_keys = _payload_shape(raw)
        return True, str(target), payload_type, digest, top_keys, summary
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        return False, None, None, None, None, None


def check_collectors(settings):
    """Executa todas as casas de forma resiliente e preserva cada payload bruto."""
    results = []
    raw_dir = getattr(settings, "raw_data_dir", "data/raw")
    save_raw = bool(getattr(settings, "save_raw_json", True))

    for collector in build_collectors(settings):
        started = time.perf_counter()
        bookmaker = getattr(
            collector,
            "sportsbook_name",
            getattr(collector, "bookmaker", collector.__class__.__name__),
        )
        endpoint = getattr(collector, "api_endpoint", "")

        raw_saved = False
        raw_file = None
        payload_type = None
        payload_sha256 = None
        payload_top_keys = None
        payload_summary = None

        try:
            raw = collector.fetch_raw_data()

            if save_raw:
                (
                    raw_saved,
                    raw_file,
                    payload_type,
                    payload_sha256,
                    payload_top_keys,
                    payload_summary,
                ) = save_raw_payload(raw, raw_dir, bookmaker)

            records = collector.normalize_data(raw)
            quality = assess_records(records)
            status = "OK" if records else "EMPTY"

            results.append(
                CollectorHealthResult(
                    bookmaker=bookmaker,
                    status=status,
                    latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    records=len(records),
                    http_status=getattr(collector, "last_http_status", None),
                    error=None,
                    endpoint=endpoint,
                    response_bytes=getattr(collector, "last_response_bytes", None),
                    quality_score=float(quality.get("quality_score", 0.0)),
                    unique_events=int(quality.get("unique_events", 0)),
                    duplicate_rate_percent=float(quality.get("duplicate_rate_percent", 0.0)),
                    missing_start_percent=float(quality.get("missing_start_percent", 0.0)),
                    supported_market_percent=float(quality.get("supported_market_percent", 0.0)),
                    raw_saved=raw_saved,
                    raw_file=raw_file,
                    payload_type=payload_type,
                    payload_sha256=payload_sha256,
                    payload_top_keys=payload_top_keys,
                    payload_summary=payload_summary,
                )
            )

        except Exception as exc:
            # Uma casa com timeout/HTTP/JSON não interrompe o diagnóstico das demais.
            # Se houver resposta antes da exceção e ela tiver sido capturada pelo collector,
            # os metadados de status/bytes continuam disponíveis.
            results.append(
                CollectorHealthResult(
                    bookmaker=bookmaker,
                    status="ERROR",
                    latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    records=0,
                    http_status=getattr(collector, "last_http_status", None),
                    error=f"{type(exc).__name__}: {exc}",
                    endpoint=endpoint,
                    response_bytes=getattr(collector, "last_response_bytes", None),
                    raw_saved=raw_saved,
                    raw_file=raw_file,
                    payload_type=payload_type,
                    payload_sha256=payload_sha256,
                    payload_top_keys=payload_top_keys,
                    payload_summary=payload_summary,
                )
            )

    return results
