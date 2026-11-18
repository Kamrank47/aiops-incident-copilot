import time
from pathlib import Path

import httpx

from .config import Settings
from .models import Alert, Context

# Queries are templated on the alert's `service` label.
METRIC_QUERIES = {
    "error_rate_5m": 'sum(rate(http_requests_total{{service="{svc}",code=~"5.."}}[5m]))',
    "p95_latency_s": (
        'histogram_quantile(0.95, sum by (le) '
        '(rate(http_request_duration_seconds_bucket{{service="{svc}"}}[5m])))'
    ),
    "memory_bytes": 'sum(container_memory_working_set_bytes{{pod=~"{svc}.*"}})',
    "restarts_1h": 'sum(increase(kube_pod_container_status_restarts_total{{pod=~"{svc}.*"}}[1h]))',
}


async def _prom_value(client: httpx.AsyncClient, base: str, query: str) -> str:
    try:
        r = await client.get(f"{base}/api/v1/query", params={"query": query})
        result = r.json()["data"]["result"]
        return result[0]["value"][1] if result else "no data"
    except Exception:  # context is best-effort; never block triage
        return "unavailable"


async def _loki_lines(client: httpx.AsyncClient, s: Settings, svc: str) -> list[str]:
    now = time.time_ns()
    params = {
        "query": f'{{service="{svc}"}} |~ "(?i)error|exception|fatal|timeout"',
        "start": str(now - 30 * 60 * 1_000_000_000),
        "end": str(now),
        "limit": str(s.max_log_lines),
        "direction": "backward",
    }
    try:
        r = await client.get(f"{s.loki_url}/loki/api/v1/query_range", params=params)
        streams = r.json()["data"]["result"]
        return [line for st in streams for _, line in st["values"]][: s.max_log_lines]
    except Exception:
        return []


def load_runbook(alert_name: str, runbook_dir: str) -> str:
    path = Path(runbook_dir) / f"{alert_name}.md"
    return path.read_text() if path.is_file() else ""


async def gather_context(alert: Alert, s: Settings) -> Context:
    svc = alert.labels.get("service", "unknown")
    async with httpx.AsyncClient(timeout=5) as client:
        metrics = {
            name: await _prom_value(client, s.prometheus_url, tpl.format(svc=svc))
            for name, tpl in METRIC_QUERIES.items()
        }
        logs = await _loki_lines(client, s, svc)
    return Context(metrics=metrics, log_lines=logs, recent_deploys=[])
